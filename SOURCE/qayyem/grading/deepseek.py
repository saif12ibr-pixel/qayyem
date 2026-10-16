"""DeepSeek implementation of the Grader interface.

DeepSeek serves an OpenAI-compatible chat-completions API, so this reuses the
OpenAI grader wholesale and changes only the endpoint, the default model and the
wording of its errors. Duplicating the request, retry and validation logic would
mean two copies to keep in step for no benefit.
"""
import requests

from .base import GraderConfigError, GraderTransientError
from .openai import OpenAIGrader

BASE_URL = "https://api.deepseek.com"
ENDPOINT = BASE_URL + "/v1/chat/completions"
LIST_ENDPOINT = BASE_URL + "/v1/models"


class DeepSeekGrader(OpenAIGrader):
    provider_label = "DeepSeek"

    def __init__(self, api_key, model="deepseek-chat", session=None):
        if not api_key:
            raise GraderConfigError(
                "No DeepSeek API key is set. Add one on the Settings page, or set "
                "DEEPSEEK_API_KEY in .env. Keys come from "
                "https://platform.deepseek.com/api_keys"
            )
        super().__init__(api_key, model=model, session=session)

    def _endpoint(self):
        return ENDPOINT


def list_models(api_key, session=None):
    """Return the DeepSeek model ids this key can use."""
    if not api_key:
        raise GraderConfigError("A DeepSeek API key is needed to list models.")
    http = session or requests
    resp = http.get(
        LIST_ENDPOINT,
        headers={"Authorization": "Bearer " + api_key},
        timeout=30,
    )
    if resp.status_code in (401, 403):
        raise GraderConfigError("DeepSeek rejected the key while listing models.")
    if resp.status_code != 200:
        raise GraderTransientError(
            "Could not list DeepSeek models ({0}).".format(resp.status_code)
        )
    return sorted({entry.get("id") for entry in (resp.json().get("data") or []) if entry.get("id")})
