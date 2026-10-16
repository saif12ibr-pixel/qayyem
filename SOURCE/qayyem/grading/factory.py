"""Selects the grader named by configuration or by the instructor's settings.

Keeping this the only place that maps a provider name to a class is what makes
switching providers a configuration change rather than a code change.
"""
from .base import GraderConfigError
from .claude import ClaudeGrader
from .deepseek import DeepSeekGrader
from .fake import FakeGrader
from .gemini import GeminiGrader
from .openai import OpenAIGrader

# Providers an instructor may choose in the interface. "fake" is deliberately
# absent: it performs no inference and exists only for the test suite, so
# offering it in the UI would invite someone to demonstrate it as real grading.
SELECTABLE_PROVIDERS = (
    {
        "name": "gemini",
        "title": "Google Gemini",
        "note": "Free tier available. No payment card needed.",
        # Stated here rather than discovered halfway through a class: the free
        # tier caps requests per minute and per day, and a large upload can stop
        # partway when that cap is reached.
        "warning": (
            "The free tier limits how many requests you may send per minute and "
            "per day. Grading a large class can reach that limit and stop part "
            "way through. If it does, your uploaded responses are kept and you "
            "can grade again once the limit resets."
        ),
    },
    {
        "name": "openai",
        "title": "OpenAI GPT-4o",
        "note": "Requires a paid OpenAI account with billing enabled.",
        "warning": (
            "Usage is charged to your own OpenAI account. Short answers cost very "
            "little, but the cost is yours and rises with the number of students."
        ),
    },
    {
        "name": "claude",
        "title": "Anthropic Claude",
        "note": "Requires a paid Anthropic account.",
        "warning": (
            "Usage is charged to your own Anthropic account. Claude handles Arabic "
            "well, but it has no free tier, so every graded class costs money."
        ),
    },
    {
        "name": "deepseek",
        "title": "DeepSeek",
        "note": "Paid, but among the cheapest options.",
        "warning": (
            "Usage is charged to your own DeepSeek account. It is inexpensive, but "
            "note that requests are processed on servers in China -- check that your "
            "university permits sending student work there before using it."
        ),
    },
)

# "-latest" aliases track whichever model is current, so a retirement does not
# break the application. Pinning gemini-2.0-flash did exactly that: Google
# withdrew it and every grading run failed with a 404.
DEFAULT_MODELS = {
    "claude": "claude-opus-5-5",
    "deepseek": "deepseek-chat",
    # flash-lite, not flash: short answers graded in bulk do not need the larger
    # model, and the lite tier has a more generous free-tier allowance, which is
    # the binding constraint here. The plain flash alias was also returning 503
    # "high demand" while lite answered normally.
    "gemini": "gemini-flash-lite-latest",
    "openai": "gpt-4o",
}

# Offered before a key exists, so the model field is never an empty box someone
# has to guess at. Providers add and retire models constantly, so these are a
# starting point -- `list_models` asks the account itself and is authoritative.
KNOWN_MODELS = {
    # The 2.5 family is omitted: it returns 404 "no longer available to new
    # users", so offering it would hand new accounts a broken choice.
    "gemini": [
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
    ],
    "claude": [
        "claude-opus-5-5",
        "claude-sonnet-5-5",
        "claude-haiku-4-5",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-reasoner",
    ],
}


def list_models(provider, api_key):
    """Ask a provider which models the given key may actually use.

    Typing a model name by hand is easy to get wrong, and a wrong name only
    surfaces as a 404 once grading is already running against a real class.
    Listing from the account removes that whole class of failure.
    """
    name = (provider or "").strip().lower()
    if name == "gemini":
        from .gemini import list_models as _list
        return _list(api_key)
    if name == "openai":
        from .openai import list_models as _list
        return _list(api_key)
    if name == "claude":
        from .claude import list_models as _list
        return _list(api_key)
    if name == "deepseek":
        from .deepseek import list_models as _list
        return _list(api_key)
    raise GraderConfigError("Cannot list models for provider '" + name + "'.")


def build_grader(config, provider=None, api_key=None, model=None):
    """Return a Grader.

    `provider`, `api_key` and `model` override the server's configuration, which
    is how an instructor's own settings take effect. Anything not overridden
    falls back to the server's .env, so the application still works for an
    instructor who has not configured anything.
    """
    name = (provider or config.get("GRADER") or "gemini").strip().lower()

    if name == "fake":
        return FakeGrader()

    if name == "gemini":
        return GeminiGrader(
            api_key or config.get("GEMINI_API_KEY", ""),
            model or config.get("GEMINI_MODEL") or DEFAULT_MODELS["gemini"],
        )

    if name == "openai":
        return OpenAIGrader(
            api_key or config.get("OPENAI_API_KEY", ""),
            model or config.get("OPENAI_MODEL") or DEFAULT_MODELS["openai"],
        )

    if name == "claude":
        return ClaudeGrader(
            api_key or config.get("ANTHROPIC_API_KEY", ""),
            model or config.get("ANTHROPIC_MODEL") or DEFAULT_MODELS["claude"],
        )

    if name == "deepseek":
        return DeepSeekGrader(
            api_key or config.get("DEEPSEEK_API_KEY", ""),
            model or config.get("DEEPSEEK_MODEL") or DEFAULT_MODELS["deepseek"],
        )

    raise GraderConfigError(
        "Unknown provider '" + name + "'. Use 'gemini', 'openai', 'claude', "
        "'deepseek' or 'fake'."
    )
