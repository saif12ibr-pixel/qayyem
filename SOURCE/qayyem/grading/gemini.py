"""Google Gemini implementation of the Grader interface.

Called over the REST API with `requests` rather than through a vendor SDK, so
there is one less dependency to pin and the HTTP behaviour (timeouts, retries,
status handling) stays visible in this file.

The API key is read from configuration, which reads it from the environment --
never from source and never sent to the browser (SS 4.3.3).
"""
import json
import random
import time

import requests

from .base import (
    Grader,
    GraderConfigError,
    GraderError,
    GraderRateLimitError,
    GraderTransientError,
)
from .prompt import RESPONSE_SCHEMA, build_prompt, validate_results

ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 90


class GeminiGrader(Grader):
    def __init__(self, api_key, model, session=None):
        if not api_key:
            raise GraderConfigError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add a "
                "free key from https://aistudio.google.com/apikey"
            )
        self.api_key = api_key
        self.model = model
        self.name = model
        self._session = session or requests.Session()

    def grade_batch(self, items, ideal_answer, rubric, max_score):
        if not items:
            return []
        prompt = build_prompt(items, ideal_answer, rubric, max_score)
        text = self._generate(prompt)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GraderError("Model did not return valid JSON: " + str(exc)) from exc
        return validate_results(parsed, [i.student_id for i in items], max_score)

    def _generate(self, prompt):
        """POST the prompt, retrying transient failures with backoff."""
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": RESPONSE_SCHEMA,
                "temperature": 0.2,
            },
        }
        url = ENDPOINT.format(model=self.model)
        last_error = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = self._session.post(
                    url,
                    json=body,
                    timeout=TIMEOUT_SECONDS,
                    headers={
                        "x-goog-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                )
            except requests.Timeout as exc:
                last_error = GraderTransientError("Request timed out: " + str(exc))
            except requests.RequestException as exc:
                last_error = GraderTransientError("Network error: " + str(exc))
            else:
                if resp.status_code == 200:
                    return self._extract_text(resp.json())
                last_error = self._classify(resp)
                if isinstance(last_error, GraderError):
                    raise last_error

            if attempt < MAX_ATTEMPTS:
                # Exponential backoff with jitter, so rate-limited batches do
                # not all retry in lockstep.
                time.sleep(min(2 ** attempt + random.uniform(0, 0.5), 30))

        raise last_error or GraderTransientError("Request failed")

    def _classify(self, resp):
        """Map an HTTP status onto a retryable or a permanent error."""
        detail = resp.text[:300]
        status = resp.status_code
        if status == 429:
            return GraderRateLimitError("Rate limited by the API (429). " + detail)
        if status >= 500:
            return GraderTransientError(
                "API server error ({0}). {1}".format(status, detail)
            )
        if status in (401, 403):
            return GraderConfigError(
                "API rejected the key ({0}). Check GEMINI_API_KEY in .env. {1}".format(
                    status, detail
                )
            )
        if status == 404:
            return GraderConfigError(
                "Model {0} was not found. Set GEMINI_MODEL in .env to a model your "
                "key can use. {1}".format(self.model, detail)
            )
        return GraderError("API returned {0}. {1}".format(status, detail))

    @staticmethod
    def _extract_text(payload):
        """Pull the text out of a Gemini response, explaining any refusal."""
        candidates = payload.get("candidates") or []
        if not candidates:
            blocked = (payload.get("promptFeedback") or {}).get("blockReason")
            if blocked:
                raise GraderError("Request was blocked by the provider: " + str(blocked))
            raise GraderError("API returned no candidates")

        candidate = candidates[0]
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            reason = candidate.get("finishReason", "unknown")
            raise GraderError(
                "API returned empty content (finishReason=" + str(reason) + ")"
            )
        return text


LIST_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


def list_models(api_key, session=None):
    """Return the model ids this key can use for grading.

    Filtered to models that support generateContent, because the list also
    contains embedding and vision-only models that would fail at grading time.
    """
    if not api_key:
        raise GraderConfigError("A Gemini API key is needed to list models.")
    http = session or requests
    resp = http.get(
        LIST_ENDPOINT,
        headers={"x-goog-api-key": api_key},
        params={"pageSize": 200},
        timeout=30,
    )
    if resp.status_code in (401, 403):
        raise GraderConfigError("Gemini rejected the key while listing models.")
    if resp.status_code != 200:
        raise GraderTransientError(
            "Could not list Gemini models ({0}).".format(resp.status_code)
        )

    # Image, speech and music models advertise generateContent too, but cannot
    # grade text, so offering them would only invite a confusing failure.
    skip = ("image", "tts", "audio", "omni", "embedding", "lyria", "banana",
            "veo", "imagen")

    models = []
    for entry in (resp.json().get("models") or []):
        methods = entry.get("supportedGenerationMethods") or []
        if "generateContent" not in methods:
            continue
        name = (entry.get("name") or "").replace("models/", "", 1)
        if not name or any(token in name for token in skip):
            continue
        models.append(name)
    return sorted(set(models))
