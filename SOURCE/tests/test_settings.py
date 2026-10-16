"""Tests for provider selection, key encryption, and the Settings page."""
import pytest

from qayyem.crypto import decrypt_key, encrypt_key, mask_key
from qayyem.db import get_db
from qayyem.grading import GraderConfigError, GraderError
from qayyem.grading.fake import FakeGrader
from qayyem.grading.factory import build_grader
from qayyem.grading.gemini import GeminiGrader
from qayyem.grading.openai import OpenAIGrader
from tests.conftest import INSTRUCTOR_EMAIL

SECRET = "test-secret-key"


# --- encryption -------------------------------------------------------------

def test_key_round_trips():
    token = encrypt_key(SECRET, "sk-abc123")
    assert decrypt_key(SECRET, token) == "sk-abc123"


def test_ciphertext_does_not_contain_the_key():
    """The point of encrypting is that the stored value does not reveal it."""
    token = encrypt_key(SECRET, "sk-supersecret-value")
    assert "supersecret" not in token


def test_wrong_secret_returns_none_rather_than_raising():
    """A changed SECRET_KEY must degrade to 'ask again', not crash grading."""
    token = encrypt_key(SECRET, "sk-abc123")
    assert decrypt_key("a-different-secret", token) is None


def test_empty_key_encrypts_to_none():
    assert encrypt_key(SECRET, "") is None
    assert decrypt_key(SECRET, None) is None


def test_mask_hides_the_middle():
    masked = mask_key("sk-1234567890abcdef")
    assert masked.startswith("sk-")
    assert masked.endswith("cdef")
    assert "1234567890" not in masked


def test_mask_of_short_key_reveals_nothing():
    assert set(mask_key("abcd")) == {"*"}


# --- factory ----------------------------------------------------------------

def test_factory_builds_openai():
    grader = build_grader({}, provider="openai", api_key="sk-test")
    assert isinstance(grader, OpenAIGrader)
    assert grader.name == "gpt-4o"


def test_factory_builds_gemini():
    grader = build_grader({}, provider="gemini", api_key="key")
    assert isinstance(grader, GeminiGrader)


def test_factory_instructor_override_beats_server_config():
    config = {"GRADER": "gemini", "GEMINI_API_KEY": "server-key"}
    grader = build_grader(config, provider="openai", api_key="sk-mine")
    assert isinstance(grader, OpenAIGrader)
    assert grader.api_key == "sk-mine"


def test_factory_falls_back_to_server_key():
    config = {"GRADER": "gemini", "GEMINI_API_KEY": "server-key"}
    grader = build_grader(config)
    assert grader.api_key == "server-key"


def test_factory_honours_custom_model():
    grader = build_grader({}, provider="openai", api_key="k", model="gpt-4o-mini")
    assert grader.model == "gpt-4o-mini"


def test_openai_requires_a_key():
    with pytest.raises(GraderConfigError, match="OpenAI API key"):
        build_grader({}, provider="openai", api_key="")


def test_unknown_provider_rejected():
    with pytest.raises(GraderConfigError, match="Unknown provider"):
        build_grader({}, provider="deepmind")


def test_fake_still_available_for_tests():
    assert isinstance(build_grader({"GRADER": "fake"}), FakeGrader)


def test_fake_is_not_offered_in_the_interface():
    """Offering it would invite demonstrating word-overlap scoring as AI."""
    from qayyem.grading.factory import SELECTABLE_PROVIDERS

    assert "fake" not in {p["name"] for p in SELECTABLE_PROVIDERS}


# --- settings page ----------------------------------------------------------

def test_settings_requires_login(client):
    response = client.get("/settings/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_settings_page_renders(client, auth):
    auth.login()
    response = client.get("/settings/")
    assert response.status_code == 200
    assert b"Grading settings" in response.data
    assert b"OpenAI GPT-4o" in response.data
    assert b"Google Gemini" in response.data


def test_saving_provider_and_key(client, app, auth):
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "openai",
                                    "model": "gpt-4o", "api_key": "sk-mykey123456"})
    with app.app_context():
        row = get_db().execute(
            "SELECT ai_provider, ai_model, api_key_enc FROM instructor WHERE email = ?",
            (INSTRUCTOR_EMAIL,),
        ).fetchone()
    assert row["ai_provider"] == "openai"
    assert row["ai_model"] == "gpt-4o"
    assert decrypt_key(app.config["SECRET_KEY"], row["api_key_enc"]) == "sk-mykey123456"


def test_stored_key_is_never_sent_to_the_browser(client, auth):
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "gemini",
                                    "model": "gemini-2.0-flash",
                                    "api_key": "sk-secret-value-9876"})
    response = client.get("/settings/")
    assert b"sk-secret-value-9876" not in response.data
    assert b"secret-value" not in response.data


def test_blank_key_field_keeps_the_saved_key(client, app, auth):
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "gemini",
                                    "model": "gemini-2.0-flash", "api_key": "sk-original"})
    # Change only the model; the key field is left empty.
    client.post("/settings/", data={"action": "save", "provider": "gemini",
                                    "model": "gemini-1.5-pro", "api_key": ""})
    with app.app_context():
        row = get_db().execute(
            "SELECT ai_model, api_key_enc FROM instructor WHERE email = ?",
            (INSTRUCTOR_EMAIL,),
        ).fetchone()
    assert row["ai_model"] == "gemini-1.5-pro"
    assert decrypt_key(app.config["SECRET_KEY"], row["api_key_enc"]) == "sk-original"


def test_clearing_the_key(client, app, auth):
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "gemini",
                                    "model": "gemini-2.0-flash", "api_key": "sk-gone"})
    client.post("/settings/", data={"action": "clear_key"})
    with app.app_context():
        row = get_db().execute(
            "SELECT api_key_enc FROM instructor WHERE email = ?", (INSTRUCTOR_EMAIL,)
        ).fetchone()
    assert row["api_key_enc"] is None


def test_invalid_provider_rejected(client, app, auth):
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "hackerman",
                                    "model": "x", "api_key": "k"})
    with app.app_context():
        row = get_db().execute(
            "SELECT ai_provider FROM instructor WHERE email = ?", (INSTRUCTOR_EMAIL,)
        ).fetchone()
    assert row["ai_provider"] != "hackerman"


def test_instructors_do_not_see_each_others_keys(client, app, auth):
    """One instructor's key must never leak into another's session."""
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "openai",
                                    "model": "gpt-4o", "api_key": "sk-alices-key-123"})
    auth.logout(confirm=True)

    client.post("/login", data={"email": "other@seu.edu.sa", "password": "password123"})
    response = client.get("/settings/")
    assert b"sk-alices-key" not in response.data
    assert b"alices" not in response.data


# --- pre-flight readiness ---------------------------------------------------

def test_readiness_false_when_no_key_anywhere(app):
    from qayyem.settings import grading_readiness
    with app.app_context():
        row = get_db().execute(
            "SELECT * FROM instructor WHERE email = ?", (INSTRUCTOR_EMAIL,)
        ).fetchone()
        status = grading_readiness({"GRADER": "gemini", "GEMINI_API_KEY": "",
                                    "SECRET_KEY": "k"}, row)
    assert status["ok"] is False
    assert "cannot run" in status["message"]


def test_readiness_true_from_server_key(app):
    from qayyem.settings import grading_readiness
    with app.app_context():
        row = get_db().execute(
            "SELECT * FROM instructor WHERE email = ?", (INSTRUCTOR_EMAIL,)
        ).fetchone()
        status = grading_readiness({"GRADER": "gemini", "GEMINI_API_KEY": "server",
                                    "SECRET_KEY": "k"}, row)
    assert status["ok"] is True
    assert "server" in status["source"]


def test_readiness_prefers_instructors_own_key(client, app, auth):
    from qayyem.settings import grading_readiness
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "openai",
                                    "model": "gpt-4o", "api_key": "sk-mine"})
    with app.app_context():
        row = get_db().execute(
            "SELECT * FROM instructor WHERE email = ?", (INSTRUCTOR_EMAIL,)
        ).fetchone()
        status = grading_readiness(
            {"GRADER": "gemini", "GEMINI_API_KEY": "server",
             "SECRET_KEY": app.config["SECRET_KEY"]}, row)
    assert status["ok"] is True
    assert status["source"] == "your own key"
    assert "GPT-4o" in status["provider"]


def test_upload_page_warns_when_grading_unavailable(client, app, auth):
    """The warning must appear before a file is uploaded, not after it fails."""
    app.config["GRADER"] = "gemini"   # a real provider, unlike the test default
    app.config["GEMINI_API_KEY"] = ""
    app.config["OPENAI_API_KEY"] = ""
    auth.login()
    response = client.get("/upload")
    assert b"Grading is not set up yet" in response.data
    assert b"Add a key" in response.data


def test_upload_page_names_the_active_provider_when_ready(client, app, auth):
    app.config["GRADER"] = "gemini"
    app.config["GEMINI_API_KEY"] = "server-key"
    auth.login()
    response = client.get("/upload")
    assert b"Grading is not set up yet" not in response.data
    assert b"Google Gemini" in response.data


def test_upload_page_says_plainly_when_the_offline_stub_is_active(client, app, auth):
    """Running the stub must be visible, not mistaken for real AI grading."""
    app.config["GRADER"] = "fake"
    auth.login()
    response = client.get("/upload")
    assert b"offline test grader" in response.data
    assert b"no AI" in response.data


# --- model listing ----------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _FakeHttp:
    """Stands in for `requests`, so listing is tested without a network call."""

    def __init__(self, response):
        self._response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self._response


def test_gemini_list_filters_to_generating_models():
    from qayyem.grading.gemini import list_models
    http = _FakeHttp(_FakeResponse(200, {"models": [
        {"name": "models/gemini-2.0-flash",
         "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/text-embedding-004",
         "supportedGenerationMethods": ["embedContent"]},
        {"name": "models/gemini-2.5-pro",
         "supportedGenerationMethods": ["generateContent", "countTokens"]},
    ]}))
    assert list_models("key", session=http) == ["gemini-2.0-flash", "gemini-2.5-pro"]


def test_gemini_list_requires_a_key():
    from qayyem.grading.gemini import list_models
    with pytest.raises(GraderConfigError, match="key is needed"):
        list_models("")


def test_gemini_list_reports_a_rejected_key():
    from qayyem.grading.gemini import list_models
    http = _FakeHttp(_FakeResponse(403))
    with pytest.raises(GraderConfigError, match="rejected the key"):
        list_models("bad", session=http)


def test_openai_list_keeps_only_chat_models():
    from qayyem.grading.openai import list_models
    http = _FakeHttp(_FakeResponse(200, {"data": [
        {"id": "gpt-4o"},
        {"id": "gpt-4o-mini"},
        {"id": "gpt-4o-audio-preview"},
        {"id": "text-embedding-3-small"},
        {"id": "dall-e-3"},
        {"id": "gpt-4o-transcribe"},
    ]}))
    assert list_models("key", session=http) == ["gpt-4o", "gpt-4o-mini"]


def test_openai_list_requires_a_key():
    from qayyem.grading.openai import list_models
    with pytest.raises(GraderConfigError, match="key is needed"):
        list_models("")


def test_factory_rejects_listing_for_unknown_provider():
    from qayyem.grading.factory import list_models as dispatch
    with pytest.raises(GraderConfigError, match="Cannot list models"):
        dispatch("deepmind", "key")


def test_curated_lists_cover_both_providers():
    from qayyem.grading.factory import DEFAULT_MODELS, KNOWN_MODELS
    for provider in ("gemini", "openai"):
        assert KNOWN_MODELS[provider], provider
        # The default must be offered, or the page opens on a value not in its
        # own list and the selection silently changes under the instructor.
        assert DEFAULT_MODELS[provider] in KNOWN_MODELS[provider], provider


def test_settings_page_renders_a_model_dropdown(client, auth):
    auth.login()
    response = client.get("/settings/")
    assert b'id="model-select"' in response.data
    assert b"gemini-flash-latest" in response.data
    assert b"gpt-4o" in response.data
    assert b"refresh_models" in response.data


def test_default_models_are_self_updating_aliases_where_available():
    """A pinned model can be retired out from under us.

    gemini-2.0-flash was withdrawn by Google mid-project and every grading run
    began failing with a 404, so the Gemini default tracks an alias instead.
    """
    from qayyem.grading.factory import DEFAULT_MODELS
    assert DEFAULT_MODELS["gemini"].endswith("-latest")


def test_gemini_listing_excludes_non_text_models():
    """Image and speech models advertise generateContent but cannot grade."""
    from qayyem.grading.gemini import list_models
    http = _FakeHttp(_FakeResponse(200, {"models": [
        {"name": "models/gemini-flash-latest",
         "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-2.5-flash-image",
         "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-3.8-flash-tts",
         "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-omni-1.1-flash",
         "supportedGenerationMethods": ["generateContent"]},
    ]}))
    assert list_models("key", session=http) == ["gemini-flash-latest"]


def test_refresh_reports_failure_without_crashing(client, app, auth):
    """A bad key must produce a message, not a 500."""
    app.config["GEMINI_API_KEY"] = ""
    auth.login()
    response = client.post("/settings/", data={
        "action": "refresh_models", "provider": "gemini", "api_key": ""},
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Could not fetch the model list" in response.data


# --- free-tier warnings -----------------------------------------------------

def test_every_provider_states_its_trade_off():
    """Cost and rate limits should be read before a class is uploaded."""
    from qayyem.grading.factory import SELECTABLE_PROVIDERS
    for entry in SELECTABLE_PROVIDERS:
        assert entry["warning"], entry["name"]


def test_gemini_warning_names_the_rate_limit_and_reassures_about_data():
    from qayyem.grading.factory import SELECTABLE_PROVIDERS
    gemini = next(p for p in SELECTABLE_PROVIDERS if p["name"] == "gemini")
    assert "free tier" in gemini["warning"].lower()
    assert "limit" in gemini["warning"].lower()
    assert "kept" in gemini["warning"].lower()


def test_openai_warning_says_the_cost_is_the_users():
    from qayyem.grading.factory import SELECTABLE_PROVIDERS
    openai = next(p for p in SELECTABLE_PROVIDERS if p["name"] == "openai")
    assert "charged" in openai["warning"].lower()


def test_settings_page_shows_the_provider_warnings(client, auth):
    auth.login()
    response = client.get("/settings/")
    assert b"provider-warning" in response.data
    assert b"free tier limits how many requests" in response.data.lower()


def test_upload_page_cautions_about_the_free_tier(client, app, auth):
    app.config["GRADER"] = "gemini"
    app.config["GEMINI_API_KEY"] = "server-key"
    auth.login()
    response = client.get("/upload")
    assert b"Free tier" in response.data
    assert b"stop part way" in response.data


def test_upload_caution_switches_with_the_provider(client, app, auth):
    app.config["OPENAI_API_KEY"] = "sk-server"
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "openai",
                                    "model": "gpt-4o", "api_key": ""})
    response = client.get("/upload")
    assert b"charged to the OpenAI account" in response.data
    assert b"Free tier" not in response.data


# --- Claude and DeepSeek providers ------------------------------------------

def test_all_four_providers_are_selectable():
    from qayyem.grading.factory import SELECTABLE_PROVIDERS
    names = [p["name"] for p in SELECTABLE_PROVIDERS]
    assert names == ["gemini", "openai", "claude", "deepseek"]


def test_every_provider_has_a_default_model_in_its_own_list():
    from qayyem.grading.factory import DEFAULT_MODELS, KNOWN_MODELS, SELECTABLE_PROVIDERS
    for entry in SELECTABLE_PROVIDERS:
        name = entry["name"]
        assert name in DEFAULT_MODELS, name
        assert DEFAULT_MODELS[name] in KNOWN_MODELS[name], name


def test_factory_builds_claude():
    from qayyem.grading.claude import ClaudeGrader
    grader = build_grader({}, provider="claude", api_key="sk-ant-test")
    assert isinstance(grader, ClaudeGrader)
    assert grader.model == "claude-opus-5-5"


def test_factory_builds_deepseek():
    from qayyem.grading.deepseek import DeepSeekGrader
    grader = build_grader({}, provider="deepseek", api_key="sk-ds-test")
    assert isinstance(grader, DeepSeekGrader)
    assert grader.model == "deepseek-chat"


def test_claude_requires_a_key():
    with pytest.raises(GraderConfigError, match="Anthropic API key"):
        build_grader({}, provider="claude", api_key="")


def test_deepseek_requires_a_key():
    with pytest.raises(GraderConfigError, match="DeepSeek API key"):
        build_grader({}, provider="deepseek", api_key="")


def test_deepseek_posts_to_its_own_endpoint_not_openais():
    """It reuses the OpenAI request shape, so the endpoint must be overridden."""
    from qayyem.grading.deepseek import DeepSeekGrader, ENDPOINT
    grader = DeepSeekGrader("sk-ds-test")
    assert grader._endpoint() == ENDPOINT
    assert "deepseek.com" in grader._endpoint()


def test_deepseek_errors_name_deepseek_not_openai():
    from qayyem.grading.deepseek import DeepSeekGrader

    class R:
        status_code = 401
        text = "bad key"

    message = str(DeepSeekGrader("sk-ds-test")._classify(R()))
    assert "DeepSeek" in message
    assert "OpenAI" not in message


def test_claude_reports_a_refusal_clearly():
    """A safety decline arrives as a normal 200, so it must be checked for."""
    from qayyem.grading.claude import ClaudeGrader

    class Response:
        stop_reason = "refusal"
        stop_details = type("D", (), {"category": "cyber"})()
        content = []

    with pytest.raises(GraderError, match="declined to grade"):
        ClaudeGrader._extract_text(Response())


def test_claude_strips_a_fenced_code_block():
    """Models sometimes wrap JSON in ``` despite being told not to."""
    from qayyem.grading.claude import ClaudeGrader

    class Block:
        type = "text"
        text = '```json\n[{"student_id": "S1", "score": 5, "feedback_ar": "x"}]\n```'

    class Response:
        stop_reason = "end_turn"
        stop_details = None
        content = [Block()]

    assert ClaudeGrader._extract_text(Response()).startswith("[")


def test_claude_raises_on_empty_content():
    from qayyem.grading.claude import ClaudeGrader

    class Response:
        stop_reason = "max_tokens"
        stop_details = None
        content = []

    with pytest.raises(GraderError, match="no text"):
        ClaudeGrader._extract_text(Response())


def test_settings_page_offers_all_four(client, auth):
    auth.login()
    response = client.get("/settings/")
    for label in (b"Google Gemini", b"OpenAI GPT-4o", b"Anthropic Claude", b"DeepSeek"):
        assert label in response.data, label
    assert b"claude-opus-5-5" in response.data
    assert b"deepseek-chat" in response.data


def test_deepseek_warning_mentions_where_data_is_processed():
    """Sending student work abroad is a decision the instructor should make."""
    from qayyem.grading.factory import SELECTABLE_PROVIDERS
    entry = next(p for p in SELECTABLE_PROVIDERS if p["name"] == "deepseek")
    assert "China" in entry["warning"]


def test_saving_claude_as_provider(client, app, auth):
    auth.login()
    client.post("/settings/", data={"action": "save", "provider": "claude",
                                    "model": "claude-opus-5-5", "api_key": "sk-ant-x"})
    with app.app_context():
        row = get_db().execute(
            "SELECT ai_provider, ai_model FROM instructor WHERE email = ?",
            (INSTRUCTOR_EMAIL,)).fetchone()
    assert row["ai_provider"] == "claude"
    assert row["ai_model"] == "claude-opus-5-5"
