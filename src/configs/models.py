services = {
    "openai": {
        "models": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini", "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002", "gpt-3.5-turbo-instruct"},
        "completion": {"gpt-3.5-turbo-instruct"},
        "chat": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini"},
        "embedding": {"text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"}
    },
    "google": {
        "models": {"gemini-pro", "gemini-1.5-pro", "gemini-1.0-pro-vision", "gemini-1.0-pro", "gemini-1.5-Flash"},
        "chat": {"gemini-pro", "gemini-1.5-pro", "gemini-1.0-pro-vision", "gemini-1.0-pro", "gemini-1.5-Flash"},
        "completion": {"gemini-pro", "gemini-1.5-pro", "gemini-1.0-pro-vision", "gemini-1.0-pro", "gemini-1.5-Flash"},
        "embedding": {"embedding-001"}
    }
}

messageRoles = {
    "chat": ["system", "user"],
    "completion": ["prompt"],
    "embedding": ["input"]
}

# Exporting services and messageRoles
__all__ = ["services", "messageRoles"]
