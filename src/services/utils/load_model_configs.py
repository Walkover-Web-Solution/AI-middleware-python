from models.mongo_connection import db

modelConfigModel = db["modelconfigurations"]

async def get_model_configurations():
    try:
        configurations = await modelConfigModel.find({}, {"_id": 0}).to_list(length=None)
        config_dict = {}
        for conf in configurations:
            if config_dict.get(conf['service']) is None: 
                config_dict[conf['service']] = {}
            config_dict[conf['service']][conf['model_name']] = conf

        return config_dict
    except Exception as error:
        print(f"Error fetching model configurations: {error}")
        return {}
    
