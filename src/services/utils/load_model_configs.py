from models.mongo_connection import db


modelConfigModel = db["modelconfigurations"]

async def get_model_configurations():
    try:
        configurations = await modelConfigModel.find({}, {"_id": 0}).to_list(length=None)
        return generate_models_config_class(configurations)
    except Exception as error:
        print(f"Error fetching model configurations:  {error}")
        return {}
    




import json

def generate_models_config_class(configurations):
    """
    Given a list of configurations from the DB (each item having
    'model', 'configuration', 'outputConfig', 'inputConfig'),
    generate a Python class definition string that has static
    methods returning those configurations.
    """

    # Start the class definition
    lines = ["class ModelsConfig:"]

    # If there are no configurations, just return an empty class
    if not configurations:
        lines.append("    pass")
        return "\n".join(lines)

    for conf in configurations:
        # Each document is something like:
        # {
        #   "_id": "...",
        #   "service": "openai",
        #   "model": "gpt-4o",
        #   "configuration": {...},
        #   "outputConfig": {...},
        #   "inputConfig": {...}
        # }

        # 1) Convert the model name into a valid Python method name
        #    e.g. "gpt-4o-mini" -> "gpt_4o_mini"
        model_name = conf["model"].replace("-", "_")
        model_name = model_name.replace(".", "_")
        
        # 2) Convert each part of the configuration to Python syntax
        #    with correct booleans (True/False) and None, rather than
        #    JSON's true/false/null
        def to_python_dict_str(data):
            # Use JSON to generate a string, then replace
            # true->True, false->False, null->None, etc.
            text = json.dumps(data, indent=4)
            text = text.replace("true", "True")
            text = text.replace("false", "False")
            text = text.replace("null", "None")
            return text
        configuration_str = to_python_dict_str(conf.get("configuration", {}))
        output_config_str = to_python_dict_str(conf.get("outputConfig", {}))
        input_config_str = to_python_dict_str(conf.get("inputConfig", {}))

        # 3) Build the method text
        #    For example:
        #
        #    @staticmethod
        #    def gpt_4o():
        #        configuration = {
        #            ...
        #        }
        #        outputConfig = {
        #            ...
        #        }
        #        inputConfig = {
        #            ...
        #        }
        #        return {
        #            "configuration": configuration,
        #            "outputConfig": outputConfig,
        #            "inputConfig": inputConfig
        #        }

        method_lines = [
            f"    @staticmethod",
            f"    def {model_name}():",
            f"        configuration = {configuration_str}",
            f"        outputConfig = {output_config_str}",
            f"        inputConfig = {input_config_str}",
            f"",
            f"        return {{",
            f"            'configuration': configuration,",
            f"            'outputConfig': outputConfig,",
            f"            'inputConfig': inputConfig",
            f"        }}"
        ]
        lines.extend(method_lines)
        lines.append("")  # blank line after each method for readability

    # Join everything into one big string
    return "\n".join(lines)


# -----------------------------------------
# HOW YOU WOULD USE IT INSIDE YOUR CODE
# -----------------------------------------
#
# Suppose you have a function that fetches the model configurations:
#
# async def get_model_configurations():
#     try:
#         configurations = await modelConfigModel.find().to_list(length=None)
#         return configurations
#     except Exception as error:
#         print(f"Error fetching model configurations: {error}")
#         return []
#
# # Then somewhere else in your code, for example in an async context:
#
# configurations = await get_model_configurations()
# python_code = generate_models_config_class(configurations)
# print(python_code)
#
# # `python_code` is now a string containing something like:
# #
# # class ModelsConfig:
# #     @staticmethod
# #     def gpt_4o():
# #         configuration = {
# #             "model": {
# #                 "field": "drop",
# #                 ...
# #             },
# #             ...
# #         }
# #         outputConfig = {
# #             ...
# #         }
# #         inputConfig = {
# #             ...
# #         }
# #         return {
# #             "configuration": configuration,
# #             "outputConfig": outputConfig,
# #             "inputConfig": inputConfig
# #         }
# #
# #     @staticmethod
# #     def gpt_4o_mini():
# #         ...
# #
# # etc.


















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
