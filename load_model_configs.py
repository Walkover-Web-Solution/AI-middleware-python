# import pymongo
# import json
# from config import Config

# # MongoDB Connection
# MONGO_URI = Config.MONGODB_CONNECTION_URI
# client = pymongo.MongoClient(MONGO_URI)
# db = client["your_db"]
# collection = db["models_configurations"]

# def fetch_model_configurations():
#     """Fetch model configurations from MongoDB."""
#     return list(collection.find({}, {"_id": 1, "config": 1}))

# def generate_model_configuration_file(models):
#     """Generate Python file with model configurations."""
#     file_content = "class ModelsConfig:\n"

#     for model in models:
#         model_name = model["_id"]
#         json_config = json.dumps(model["config"], indent=4)

#         file_content += f"""
#     @staticmethod
#     def {model_name}():
#         return {json_config}
#     """

#     with open("modelConfiguration.py", "w") as f:
#         f.write(file_content)

# if __name__ == "__main__":
#     models = fetch_model_configurations()
#     generate_model_configuration_file(models)
#     print("✅ modelConfiguration.py updated successfully!")
