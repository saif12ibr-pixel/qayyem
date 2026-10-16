"""OpenAI GPT-4o implementation of the Grader interface.

Mirrors the Gemini grader: same prompt, same validation, same retry and error
mapping. Only the HTTP shape differs, which is the point of the Grader
interface -- the rest of the application cannot tell which one is running.
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
from .prompt import build_prompt, validate_results

ENDPOINT = "https://api.openai.com/v1/chat/completions"

MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 90


class OpenAIGrader(Grader):
    # Subclasses serving an OpenAI-compatible API override these two.
    provider_label = "OpenAI"

    def _endpoint(self):
        return ENDPOINT

    def __init__(self, api_key, model="gpt-4o", session=None):
        if not api_key:
            raise GraderConfigError(
                "No OpenAI API key is set. Add one on the Settings page, or set "
                "OPENAI_API_KEY in .env. Keys come from "
                "https://platform.openai.com/api-keys"
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
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You grade short Arabic student answers and reply "
                               "only with JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            # json_object guarantees parseable JSON but always returns an object,
            # so the array arrives wrapped. validate_results unwraps it.
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        last_error = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = self._session.post(
                    self._endpoint(),
                    json=body,
                    timeout=TIMEOUT_SECONDS,
                    headers={
                        "Authorization": "Bearer " + self.api_key,
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
                time.sleep(min(2 ** attempt + random.uniform(0, 0.5), 30))

        raise last_error or GraderTransientError("Request failed")

    def _classify(self, resp):
        detail = resp.text[:300]
        status = resp.status_code
        if status == 429:
            return GraderRateLimitError(
                "Rate limited or out of quota (429). Check your " + self.provider_label
                + " billing. " + detail
            )
        if status >= 500:
            return GraderTransientError(
                "API server error ({0}). {1}".format(status, detail)
            )
        if status in (401, 403):
            return GraderConfigError(
                "{0} rejected the key ({1}). Check it on the Settings page. {2}".format(
                    self.provider_label, status, detail
                )
            )
        if status == 404:
            return GraderConfigError(
                "Model {0} was not found, or your key cannot use it. {1}".format(
                    self.model, detail
                )
            )
        return GraderError("API returned {0}. {1}".format(status, detail))

    @staticmethod
    def _extract_text(payload):
        choices = payload.get("choices") or []
        if not choices:
            raise GraderError("API returned no choices")
        message = choices[0].get("message") or {}
        text = (message.get("content") or "").strip()
        if not text:
            reason = choices[0].get("finish_reason", "unknown")
            raise GraderError(
                "API returned empty content (finish_reason=" + str(reason) + ")"
            )
        return text


LIST_ENDPOINT = "https://api.openai.com/v1/models"


def list_models(api_key, session=None):
    """Return the chat model ids this key can use for grading.

    The account's full model list also contains embedding, audio and image
    models, which cannot grade, so it is filtered to the gpt-* chat family.
    """
    if not api_key:
        raise GraderConfigError("An OpenAI API key is needed to list models.")
    http = session or requests
    resp = http.get(
        LIST_ENDPOINT,
        headers={"Authorization": "Bearer " + api_key},
        timeout=30,
    )
    if resp.status_code in (401, 403):
        raise GraderConfigError("OpenAI rejected the key while listing models.")
    if resp.status_code != 200:
        raise GraderTransientError(
            "Could not list OpenAI models ({0}).".format(resp.status_code)
        )

    skip = ("audio", "realtime", "transcribe", "tts", "image", "search", "embedding")
    models = []
    for entry in (resp.json().get("data") or []):
        name = entry.get("id") or ""
        if not name.startswith("gpt-"):
            continue
        if any(token in name for token in skip):
            continue
        models.append(name)
    return sorted(set(models))
