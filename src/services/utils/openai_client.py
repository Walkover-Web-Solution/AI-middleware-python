from openai import AsyncOpenAI

from config import Config


def get_async_openai_client(api_key, **kwargs):
    """
    Build an AsyncOpenAI client that honors the configured base URL override.
    Falls back to the default OpenAI endpoint when OPENAI_BASE_URL is unset.
    """
    client_kwargs = dict(kwargs)
    client_kwargs["api_key"] = api_key

    base_url = getattr(Config, "OPENAI_BASE_URL", None)
    if base_url:
        client_kwargs["base_url"] = base_url.rstrip("/")

    return AsyncOpenAI(**client_kwargs)
