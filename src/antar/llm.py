"""BYOK LLM client factory.

Precedence (first set wins): OPENAI -> GROQ -> ANTHROPIC -> hackathon LiteLLM.
One OpenAI-compatible client; neatlogs.wrap() traces every backend uniformly.
ANTAR_MODEL overrides the model for any backend.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import neatlogs
from openai import OpenAI

LITELLM_BASE_URL = "https://litellm.vision.aivar.app/v1"
DEFAULT_MODEL = "claude-haiku"

_BACKENDS = {
    # env var -> (base_url, default model)
    "OPENAI_API_KEY": (None, "gpt-4o"),
    "GROQ_API_KEY": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "ANTHROPIC_API_KEY": (None, "claude-sonnet-4-6"),
    "LITELLM_API_KEY": (LITELLM_BASE_URL, DEFAULT_MODEL),
}


@dataclass
class LLMConfig:
    provider: str
    model: str
    base_url: str | None
    api_key: str


def resolve_config() -> LLMConfig:
    """Pick the first available backend by precedence; honor ANTAR_BASE_URL/MODEL."""
    base_override = os.getenv("ANTAR_BASE_URL")
    model_override = os.getenv("ANTAR_MODEL")
    for env, (base, model) in _BACKENDS.items():
        key = os.getenv(env)
        if key:
            provider = env.replace("_API_KEY", "").lower()
            return LLMConfig(
                provider=provider,
                model=model_override or model,
                base_url=base_override or base,
                api_key=key,
            )
    raise RuntimeError(
        "No LLM key found. Set one of: " + ", ".join(_BACKENDS) + " (see .env.example)."
    )


def get_client() -> tuple[OpenAI, str]:
    """Return (neatlogs-wrapped OpenAI client, model). Never use a raw client."""
    cfg = resolve_config()
    client_kwargs: dict = {"api_key": cfg.api_key}
    if cfg.base_url:
        client_kwargs["base_url"] = cfg.base_url
    client = neatlogs.wrap(OpenAI(**client_kwargs))
    return client, cfg.model


def init_tracing() -> None:
    """Initialise neatlogs once per process."""
    api_key = os.environ.get("NEATLOGS_API_KEY")
    if not api_key:
        raise RuntimeError("NEATLOGS_API_KEY not set — tracing is mandatory. See .env.example.")
    neatlogs.init(api_key=api_key, workflow_name=os.getenv("NEATLOGS_WORKFLOW", "antar-agent"))
