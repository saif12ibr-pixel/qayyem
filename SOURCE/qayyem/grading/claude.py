"""Anthropic Claude implementation of the Grader interface.

Unlike the Gemini and OpenAI graders, which call their REST endpoints with
`requests`, this one uses the official `anthropic` SDK. That is Anthropic's
documented way to call the Messages API, and it gives typed errors we can map
onto the Grader error types precisely rather than by reading status codes.

The module is named `claude.py`, not `anthropic.py`, so it cannot be confused
with -- or shadow -- the installed `anthropic` package.
"""
import anthropic

from .base import (
    Grader,
    GraderConfigError,
    GraderError,
    GraderRateLimitError,
    GraderTransientError,
)
from .prompt import build_prompt, validate_results

MAX_TOKENS = 8000
SYSTEM = (
    "You grade short Arabic student answers against an ideal answer. "
    "Reply with a JSON array only, no commentary and no code fences."
)


class ClaudeGrader(Grader):
    def __init__(self, api_key, model="claude-opus-5-5", client=None):
        if not api_key and client is None:
            raise GraderConfigError(
                "No Anthropic API key is set. Add one on the Settings page, or "
                "set ANTHROPIC_API_KEY in .env. Keys come from "
                "https://console.anthropic.com/settings/keys"
            )
        self.api_key = api_key
        self.model = model
        self.name = model
        # The SDK retries connection errors, 408, 409, 429 and 5xx itself, so
        # this grader does not add a second retry loop on top of it.
        self._client = client or anthropic.Anthropic(api_key=api_key, max_retries=2)

    def grade_batch(self, items, ideal_answer, rubric, max_score, parts=None):
        if not items:
            return []
        prompt = build_prompt(items, ideal_answer, rubric, max_score, parts)

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.AuthenticationError as exc:
            raise GraderConfigError(
                "Anthropic rejected the key. Check it on the Settings page. " + str(exc)[:200]
            ) from exc
        except anthropic.PermissionDeniedError as exc:
            raise GraderConfigError(
                "This Anthropic key lacks permission for that model. " + str(exc)[:200]
            ) from exc
        except anthropic.NotFoundError as exc:
            raise GraderConfigError(
                "Model " + str(self.model) + " was not found, or your key cannot "
                "use it. " + str(exc)[:200]
            ) from exc
        except anthropic.RateLimitError as exc:
            raise GraderRateLimitError(
                "Rate limited or out of credit (429). " + str(exc)[:200]
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise GraderTransientError("Network error: " + str(exc)[:200]) from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500:
                raise GraderTransientError(
                    "API server error ({0}). {1}".format(exc.status_code, str(exc)[:200])
                ) from exc
            raise GraderError(
                "API returned {0}. {1}".format(exc.status_code, str(exc)[:200])
            ) from exc

        text = self._extract_text(response)
        import json

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GraderError("Model did not return valid JSON: " + str(exc)) from exc
        return validate_results(parsed, [i.student_id for i in items], max_score, parts)

    @staticmethod
    def _extract_text(response):
        """Pull the reply text out, explaining a refusal rather than crashing."""
        # A safety decline arrives as a normal 200 with stop_reason "refusal",
        # so the stop reason has to be checked before reading the content.
        if getattr(response, "stop_reason", None) == "refusal":
            details = getattr(response, "stop_details", None)
            category = getattr(details, "category", None) if details else None
            raise GraderError(
                "Anthropic declined to grade this batch"
                + (" (" + str(category) + ")" if category else "")
                + ". Check that the student responses contain nothing the model "
                "would refuse to process."
            )

        parts = [b.text for b in (response.content or []) if getattr(b, "type", "") == "text"]
        text = "".join(parts).strip()
        if not text:
            raise GraderError(
                "Anthropic returned no text (stop_reason="
                + str(getattr(response, "stop_reason", "unknown")) + ")"
            )

        # Models sometimes wrap JSON in a fenced block despite the instruction.
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3]
        return text.strip()


def list_models(api_key, client=None):
    """Return the Claude model ids this key can use.

    The Models API reports what the account may actually call, which is more
    reliable than a hardcoded list that goes stale as models are released.
    """
    if not api_key and client is None:
        raise GraderConfigError("An Anthropic API key is needed to list models.")
    sdk = client or anthropic.Anthropic(api_key=api_key)
    try:
        return sorted(model.id for model in sdk.models.list())
    except anthropic.AuthenticationError as exc:
        raise GraderConfigError("Anthropic rejected the key while listing models.") from exc
    except anthropic.APIStatusError as exc:
        raise GraderTransientError(
            "Could not list Anthropic models ({0}).".format(exc.status_code)
        ) from exc
