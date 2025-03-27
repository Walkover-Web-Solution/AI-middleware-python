from src.configs.modelConfiguration import ModelsConfig
import json
import asyncio
from models.mongo_connection import db
modelconfigurations = db['modelconfigurations']

services = {
    "openai": {
        "models": {"gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o","chatgpt-4o-latest", "gpt-4-turbo", "gpt-4-0613", "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09","gpt-4o-mini", "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002", "gpt-3.5-turbo-instruct","gpt-4o-mini-2024-07-18","gpt-4o-2024-08-06", "o1-preview", "o1-mini", "o1","o3-mini","dall-e-2","dall-e-3", "gpt-4o-mini-search-preview", "gpt-4o-search-preview"}
    },
    "anthropic" : {
        "models": {"claude-3-5-sonnet-latest","claude-3-opus-latest","claude-3-opus-20240229","claude-3-5-sonnet-20241022","claude-3-sonnet-20240229", "claude-3-haiku-20240307","claude-3-5-haiku-20241022","claude-3-5-haiku-latest","claude-3-7-sonnet-latest"}
    },
    "groq" : {
        "models": {"llama-3.1-405b-reasoning", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-groq-70b-8192-tool-use-preview","llama3-groq-8b-8192-tool-use-preview","llama3-70b-8192","llama3-8b-8192","mixtral-8x7b-32768","gemma-7b-it","gemma2-9b-it","whisper-large-v3", "llama-guard-3-8b", "deepseek-r1-distill-llama-70b", "deepseek-r1-distill-qwen-32b", "qwen-2.5-32b", "qwen-2.5-coder-32b"},
    }
}


async def generate_models_json():
    print("in here")
    methods = [method for method in dir(ModelsConfig) if callable(getattr(ModelsConfig, method)) 
               and not method.startswith('__')]

    for method in methods:
        try:
            model_config = getattr(ModelsConfig, method)()
            model_config["model_name"] = model_config['configuration']['model']['default']
            
            # Determine the service for the model
            model_name = model_config["model_name"]
            for service_name, service_data in services.items():
                if model_name in service_data["models"]:
                    model_config['service'] = service_name
                    break
            
            # Save each model config to MongoDB
            await modelconfigurations.update_one(
                {"model_name": model_config["model_name"]},
                {"$set": model_config},
                upsert=True
            )
            print(f"Saved config for {model_config['model_name']}")
            
        except Exception as e:
            print(f"Failed to load/save model config: {e}")

    return {"status": "completed"}

if __name__ == "__main__":
    # Create event loop and run the async function
    loop = asyncio.get_event_loop()
    all_model_configs = loop.run_until_complete(generate_models_json())

    # Output to console
    print(json.dumps(all_model_configs, indent=2))

