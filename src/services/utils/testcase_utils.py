from src.services.commonServices.baseService.baseService import BaseService


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
    
    