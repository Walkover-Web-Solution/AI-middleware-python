from src.configs.serviceKeys import ServiceKeys

def tool_call_formatter(configuration: dict, service: str) -> dict:
    if service == 'openai':
        return  [
            {
                'type': transformed_tool['type'],
                'function': {
                    'name': transformed_tool['name'],
                    'description': transformed_tool['description'],
                    'parameters': {
                        'properties': transformed_tool.get('properties', {}),
                        'required': transformed_tool.get('required', [])
                    }
                }
            } for transformed_tool in configuration.get('tools', [])
        ]
    elif service == 'Claude':
        return  [
            {
                'name': transformed_tool['name'],
                'description': transformed_tool['description'],
                'input_schema': {
                    "type": "object",
                    'properties': transformed_tool.get('properties', {}),
                    'required': transformed_tool.get('required', [])
                }
            } for transformed_tool in configuration.get('tools', [])
        ]

def service_formatter(configuration : object, service : str ):
    try:
        new_config = {ServiceKeys[service].get(key, key): value for key, value in configuration.items()}
        new_config['tools'] = tool_call_formatter(configuration, service)
        return new_config
    except KeyError as e:
        print(f"Service key error: {e}")
        return {}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}
