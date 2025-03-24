from src.configs.modelConfiguration import ModelsConfig
import json
import asyncio
from models.mongo_connection import db
modelconfigurations = db['modelconfigurations']

async def generate_models_json():
    print("in here")
    methods = [method for method in dir(ModelsConfig) if callable(getattr(ModelsConfig, method)) 
               and not method.startswith('__')]

    for method in methods:
        try:
            model_config = getattr(ModelsConfig, method)()
            model_config["model_name"] = model_config['configuration']['model']['default']
            
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

