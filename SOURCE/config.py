"""Configuration loaded from environment variables.

The OpenAI/Gemini API key is read from the environment and never hard-coded,
per non-functional requirement SS 4.3.3 (Security Requirements).
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    GRADER = os.environ.get("GRADER", "gemini")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5")
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    SESSION_TIMEOUT_MINUTES = _int("SESSION_TIMEOUT_MINUTES", 30)
    GRADING_BATCH_SIZE = _int("GRADING_BATCH_SIZE", 10)
    MAX_ROWS = _int("MAX_ROWS", 500)

    DATABASE = os.environ.get("DATABASE")  # set by app factory when None
