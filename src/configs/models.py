services = {
    "openai": {
        "models": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o","chatgpt-4o-latest", "gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini", "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002", "gpt-3.5-turbo-instruct","gpt-4o-mini-2024-07-18","gpt-4o-2024-08-06", "o1-preview", "o1-mini", "o1","o3-mini","dall-e-2","dall-e-3", "gpt-4o-mini-search-preview", "gpt-4o-search-preview", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"},
        "completion": {"gpt-3.5-turbo-instruct"},
        "chat": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o","chatgpt-4o-latest","gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini","gpt-4o-mini-2024-07-18","gpt-4o-2024-08-06","o1-preview", "o1-mini", "o1", "o3-mini", "gpt-4o-mini-search-preview", "gpt-4o-search-preview", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"},
        "embedding": {"text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"},
        "image" : {"dall-e-2","dall-e-3"}
    },
    "openai_response": {
        "models": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o","chatgpt-4o-latest", "gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini", "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002", "gpt-3.5-turbo-instruct","gpt-4o-mini-2024-07-18","gpt-4o-2024-08-06", "o1-preview", "o1-mini", "o1","o3-mini","dall-e-2","dall-e-3", "gpt-4o-mini-search-preview", "gpt-4o-search-preview", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"},
        "completion": {"gpt-3.5-turbo-instruct"},
        "chat": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o","chatgpt-4o-latest","gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini","gpt-4o-mini-2024-07-18","gpt-4o-2024-08-06","o1-preview", "o1-mini", "o1", "o3-mini", "gpt-4o-mini-search-preview", "gpt-4o-search-preview", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"},
        "embedding": {"text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"},
        "image" : {"dall-e-2","dall-e-3"}
    },
    "google": {
        "models": {"gemini-pro", "gemini-1.5-pro", "gemini-1.0-pro-vision", "gemini-1.0-pro", "gemini-1.5-Flash"},
        "chat": {"gemini-pro", "gemini-1.5-pro", "gemini-1.0-pro-vision", "gemini-1.0-pro", "gemini-1.5-Flash"},
        "completion": {"gemini-pro", "gemini-1.5-pro", "gemini-1.0-pro-vision", "gemini-1.0-pro", "gemini-1.5-Flash"},
        "embedding": {"embedding-001"}
    },
    "anthropic" : {
        "models": {"claude-3-5-sonnet-latest","claude-3-opus-latest","claude-3-opus-20240229","claude-3-5-sonnet-20241022","claude-3-sonnet-20240229", "claude-3-haiku-20240307","claude-3-5-haiku-20241022","claude-3-5-haiku-latest","claude-3-7-sonnet-latest"},
        "chat": {"claude-3-5-sonnet-latest","claude-3-opus-latest","claude-3-opus-20240229","claude-3-5-sonnet-20241022","claude-3-sonnet-20240229", "claude-3-haiku-20240307","claude-3-5-haiku-20241022","claude-3-5-haiku-latest", "claude-3-7-sonnet-latest"}
    },
    "groq" : {
        "models": {"llama-3.1-405b-reasoning", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-groq-70b-8192-tool-use-preview","llama3-groq-8b-8192-tool-use-preview","llama3-70b-8192","llama3-8b-8192","mixtral-8x7b-32768","gemma-7b-it","gemma2-9b-it","whisper-large-v3", "llama-guard-3-8b", "deepseek-r1-distill-llama-70b", "deepseek-r1-distill-qwen-32b", "qwen-2.5-32b", "qwen-2.5-coder-32b", "meta-llama/llama-4-scout-17b-16e-instruct"},
        "chat": {"llama-3.1-405b-reasoning", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "llama3-groq-70b-8192-tool-use-preview","llama3-groq-8b-8192-tool-use-preview","llama3-70b-8192","llama3-8b-8192","mixtral-8x7b-32768","gemma-7b-it","gemma2-9b-it","whisper-large-v3", "deepseek-r1-distill-llama-70b", "deepseek-r1-distill-qwen-32b", "qwen-2.5-32b", "qwen-2.5-coder-32b", "meta-llama/llama-4-scout-17b-16e-instruct"}
    }
}

messageRoles = {
    "chat": ["system", "user"],
    "completion": ["prompt"],
    "embedding": ["input"]
}

# Exporting services and messageRoles
__all__ = ["services", "messageRoles"]
