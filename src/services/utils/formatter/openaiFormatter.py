from src.configs.serviceKeys import ServiceKeys

def format_for_openai(configuration: dict, service: str) -> dict:
    new_config = {}
    for key in configuration:
        new_config[ServiceKeys.gpt_keys.get(key, key)] = configuration[key]
    
    if service == 'openai':
        new_config['tools'] = [
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
        
        # Clean up parameters if properties and required are empty
        for tool in new_config['tools']:
            parameters = tool['function']['parameters']
            if not parameters['properties'] and not parameters['required']:
                del tool['function']['parameters']
   
    elif service == 'Claude':
        new_config['tools'] = [
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

    return new_config
