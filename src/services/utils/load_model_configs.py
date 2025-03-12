from models.mongo_connection import db

modelConfigModel = db["modelconfigurations"]

async def get_model_configurations():
    try:
        configurations = await modelConfigModel.find({}, {"_id": 0}).to_list(length=None)
        # Transform the list of configurations into a dictionary keyed by model name
        config_dict = {conf["model"]: conf for conf in configurations}
        return config_dict
    except Exception as error:
        print(f"Error fetching model configurations: {error}")
        return {}
    
