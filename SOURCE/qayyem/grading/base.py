"""The grading interface every provider implements.

Only this package knows that an external AI provider exists. The rest of the
application depends on `Grader.grade_batch` alone, so changing provider is a
configuration change rather than a code change.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class GraderError(Exception):
    """A permanent failure. Retrying will not help."""


class GraderConfigError(GraderError):
    """Missing or invalid configuration, e.g. no API key."""


class GraderTransientError(Exception):
    """A temporary failure such as a 5xx. Retrying may help."""


class GraderRateLimitError(GraderTransientError):
    """The provider is refusing because too many requests were sent.

    Separated from other transient errors because the correct response is the
    opposite: a 5xx invites a retry, while a 429 means anything that sends MORE
    requests -- retrying, or splitting a batch into individual calls -- makes
    the situation worse and burns quota that is often daily.
    """


@dataclass(frozen=True)
class ResponseItem:
    """One student answer awaiting a grade."""

    student_id: str
    response_text: str


@dataclass(frozen=True)
class GradeResult:
    """The outcome for one student.

    `score` is None when grading failed for this student; `error` then explains
    why. A failed item never aborts the rest of the batch.
    """

    student_id: str
    score: Optional[float]
    feedback_ar: str
    error: Optional[str] = None


class Grader(ABC):
    """Grades a batch of student responses against an ideal answer."""

    name: str = "grader"

    @abstractmethod
    def grade_batch(
        self,
        items: list[ResponseItem],
        ideal_answer: str,
        rubric: str,
        max_score: float,
    ) -> list[GradeResult]:
        """Return one GradeResult per item, in any order.

        Implementations must return a result for every student_id they were
        given. Raise GraderTransientError for retryable failures and
        GraderError for permanent ones.
        """
