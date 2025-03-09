from src.services.commonServices.baseService.baseService import BaseService
import json

def add_prompt_and_conversations(custom_config, conversations, service, prompt):
    custom_config['messages'] = custom_messages(custom_config, conversations, service, prompt)
    base_service = BaseService({})
    return base_service.service_formatter(custom_config, service)
    
def custom_messages(custom_config, conversations, service, prompt):
    messages = []
    match service:
            case 'openai':
                messages = [ {"role": "developer", "content": prompt }] + conversations
            case 'anthropic':
                custom_config['system'] = prompt
                messages =  conversations
            case 'groq': 
                messages = [{"role": "system", "content": prompt}] + conversations
    return messages
    
def make_json_serializable(data):
    """Recursively converts non-serializable values in a dictionary to strings."""
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(v) for v in data]
    try:
        json.dumps(data)  # Check if serializable
        return data
    except (TypeError, OverflowError):
        return str(data)