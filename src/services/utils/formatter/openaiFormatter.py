from src.configs.serviceKeys import ServiceKeys

def format_for_openai(configuration : object):
    new_config = {}
    for key in configuration : 
        new_config[ServiceKeys.gpt_keys.get(key, key)] = configuration[key]

    return new_config