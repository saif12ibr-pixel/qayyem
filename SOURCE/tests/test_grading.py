"""Tests for prompt building and validation of the model's reply.

The validation tests matter most: batching several students into one call is
what keeps the system inside free-tier rate limits, and these are the checks
that stop a batch from silently attributing one student's grade to another.
"""
import pytest

from qayyem.grading import GraderConfigError, ResponseItem
from qayyem.grading.factory import build_grader
from qayyem.grading.fake import FakeGrader
from qayyem.grading.prompt import build_prompt, validate_results

IDEAL = "Photosynthesis converts light energy into chemical energy in plants."


def items(*pairs):
    return [ResponseItem(sid, text) for sid, text in pairs]


def test_prompt_includes_ideal_answer_rubric_and_max_score():
    prompt = build_prompt(items(("S1", "answer")), IDEAL, "Award 5 for accuracy.", 20)
    assert IDEAL in prompt
    assert "Award 5 for accuracy." in prompt
    assert "20" in prompt
    assert "S1" in prompt


def test_prompt_supplies_default_criteria_when_rubric_blank():
    prompt = build_prompt(items(("S1", "a")), IDEAL, "", 10)
    assert "No explicit rubric was supplied" in prompt


def test_prompt_contains_every_student_in_the_batch():
    prompt = build_prompt(items(("S1", "a"), ("S2", "b"), ("S3", "c")), IDEAL, "", 10)
    for sid in ("S1", "S2", "S3"):
        assert sid in prompt


def test_validate_accepts_well_formed_reply():
    raw = [
        {"student_id": "S1", "score": 8, "feedback_ar": "جيد"},
        {"student_id": "S2", "score": 4.5, "feedback_ar": "مقبول"},
    ]
    results = validate_results(raw, ["S1", "S2"], 10)
    assert [r.student_id for r in results] == ["S1", "S2"]
    assert results[0].score == 8
    assert results[1].score == 4.5
    assert all(r.error is None for r in results)


def test_validate_returns_results_in_requested_order():
    """The model may reply out of order; rows must still line up with students."""
    raw = [
        {"student_id": "S2", "score": 2, "feedback_ar": "x"},
        {"student_id": "S1", "score": 9, "feedback_ar": "y"},
    ]
    results = validate_results(raw, ["S1", "S2"], 10)
    assert [r.student_id for r in results] == ["S1", "S2"]
    assert results[0].score == 9


def test_validate_flags_missing_student():
    results = validate_results([{"student_id": "S1", "score": 5, "feedback_ar": "a"}],
                               ["S1", "S2"], 10)
    assert results[1].student_id == "S2"
    assert results[1].score is None
    assert "no result" in results[1].error


def test_validate_ignores_invented_student():
    """A student we never sent must not be attributed a grade."""
    raw = [
        {"student_id": "S1", "score": 5, "feedback_ar": "a"},
        {"student_id": "GHOST", "score": 10, "feedback_ar": "b"},
    ]
    results = validate_results(raw, ["S1"], 10)
    assert len(results) == 1
    assert results[0].student_id == "S1"


def test_validate_clamps_out_of_range_score():
    results = validate_results([{"student_id": "S1", "score": 99, "feedback_ar": "a"}],
                               ["S1"], 10)
    assert results[0].score == 10
    assert "outside" in results[0].error


def test_validate_clamps_negative_score():
    results = validate_results([{"student_id": "S1", "score": -4, "feedback_ar": "a"}],
                               ["S1"], 10)
    assert results[0].score == 0


def test_validate_rejects_non_numeric_score():
    results = validate_results([{"student_id": "S1", "score": "good", "feedback_ar": "a"}],
                               ["S1"], 10)
    assert results[0].score is None
    assert "non-numeric" in results[0].error


def test_validate_flags_empty_feedback():
    results = validate_results([{"student_id": "S1", "score": 5, "feedback_ar": "  "}],
                               ["S1"], 10)
    assert "empty feedback" in results[0].error


def test_validate_handles_non_list_reply():
    results = validate_results({"unexpected": True}, ["S1"], 10)
    assert results[0].score is None


def test_validate_ignores_duplicate_entries_for_one_student():
    raw = [
        {"student_id": "S1", "score": 3, "feedback_ar": "first"},
        {"student_id": "S1", "score": 9, "feedback_ar": "second"},
    ]
    results = validate_results(raw, ["S1"], 10)
    assert len(results) == 1
    assert results[0].score == 3


def test_fake_grader_is_deterministic():
    grader = FakeGrader()
    batch = items(("S1", IDEAL), ("S2", "completely unrelated text"))
    first = grader.grade_batch(batch, IDEAL, "", 10)
    second = grader.grade_batch(batch, IDEAL, "", 10)
    assert [r.score for r in first] == [r.score for r in second]


def test_fake_grader_scores_matching_answer_above_unrelated_one():
    grader = FakeGrader()
    results = grader.grade_batch(
        items(("S1", IDEAL), ("S2", "zzz qqq")), IDEAL, "", 10
    )
    assert results[0].score > results[1].score


def test_fake_grader_returns_one_result_per_item():
    grader = FakeGrader()
    results = grader.grade_batch(items(("S1", "a"), ("S2", "b"), ("S3", "c")), IDEAL, "", 10)
    assert [r.student_id for r in results] == ["S1", "S2", "S3"]


def test_factory_builds_fake_grader():
    assert isinstance(build_grader({"GRADER": "fake"}), FakeGrader)


def test_factory_rejects_unknown_grader():
    with pytest.raises(GraderConfigError, match="Unknown provider"):
        build_grader({"GRADER": "nonsense"})


def test_factory_requires_api_key_for_gemini():
    with pytest.raises(GraderConfigError, match="GEMINI_API_KEY"):
        build_grader({"GRADER": "gemini", "GEMINI_API_KEY": "", "GEMINI_MODEL": "m"})


# --- rate-limit handling ----------------------------------------------------

def test_rate_limit_error_is_a_transient_error():
    """Existing handlers that catch transient errors must still catch it."""
    from qayyem.grading import GraderRateLimitError, GraderTransientError
    assert issubclass(GraderRateLimitError, GraderTransientError)


def test_gemini_maps_429_to_rate_limit_error():
    from qayyem.grading import GraderRateLimitError
    from qayyem.grading.gemini import GeminiGrader

    class R:
        status_code = 429
        text = "quota exceeded"

    grader = GeminiGrader("key", "m")
    assert isinstance(grader._classify(R()), GraderRateLimitError)


def test_gemini_maps_503_to_plain_transient_error():
    """A 5xx should still fan out to individual retries; only 429 must not."""
    from qayyem.grading import GraderRateLimitError, GraderTransientError
    from qayyem.grading.gemini import GeminiGrader

    class R:
        status_code = 503
        text = "high demand"

    error = GeminiGrader("key", "m")._classify(R())
    assert isinstance(error, GraderTransientError)
    assert not isinstance(error, GraderRateLimitError)


def test_openai_maps_429_to_rate_limit_error():
    from qayyem.grading import GraderRateLimitError
    from qayyem.grading.openai import OpenAIGrader

    class R:
        status_code = 429
        text = "insufficient_quota"

    assert isinstance(OpenAIGrader("sk-x", "m")._classify(R()), GraderRateLimitError)
