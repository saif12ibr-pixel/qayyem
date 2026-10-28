"""A deterministic offline grader used by the automated tests.

This exists so the whole pipeline -- parsing, batching, persistence, progress
reporting, Excel export -- can be tested without a network call, an API key, or
any cost, and so results are identical on every run.

It scores by word overlap with the ideal answer. That is a crude heuristic, not
an assessment method.

IMPORTANT: this is for development and testing only. It performs no AI
inference and must never be presented as the system's grading.
"""
import re

from .base import GradeResult, Grader, ResponseItem

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# "A good answer covering most of the required points."
_STRONG = (
    "إجابة جيدة تغطي "
    "معظم النقاط "
    "المطلوبة."
)
# "The answer is partly correct and needs more detail."
_PARTIAL = (
    "الإجابة صحيحة "
    "جزئيًا وتحتاج "
    "إلى مزيد من "
    "التفصيل."
)
# "The answer is far from what was required and needs review of the material."
_WEAK = (
    "الإجابة بعيدة "
    "عن المطلوب وتحتاج "
    "إلى مراجعة المادة."
)


def _words(text):
    return set(_WORD.findall((text or "").lower()))


class FakeGrader(Grader):
    name = "fake-offline-grader"

    def grade_batch(self, items, ideal_answer, rubric, max_score, parts=None):
        ideal = _words(ideal_answer)
        results = []
        for item in items:
            answer = _words(item.response_text)
            overlap = len(ideal & answer) / len(ideal) if ideal else 0.0
            part_scores = None
            if parts:
                # The same overlap applied to each part, so the parts sum to
                # what the whole question would have scored.
                part_scores = tuple(round(overlap * float(p["marks"]), 2) for p in parts)
                score = round(sum(part_scores), 2)
            else:
                score = round(overlap * float(max_score), 2)
            if overlap >= 0.7:
                feedback = _STRONG
            elif overlap >= 0.3:
                feedback = _PARTIAL
            else:
                feedback = _WEAK
            results.append(GradeResult(item.student_id, score, feedback,
                                       part_scores=part_scores))
        return results
