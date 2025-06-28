from src.configs.modelConfiguration import ModelsConfig as model_configuration
from ...configs.constant import service_name
from fastapi import HTTPException
from src.configs.model_configuration import model_config_document

async def get_default_values_controller(service, model, current_configuration, type):
    try:
        service = service.lower()
        
        def get_default_values(config):
            default_values = {}
            config_items = config.get('configuration', {})
            
            for key, value in config_items.items():
                current_value = current_configuration.get(key)
                
                if current_value == "min":
                    default_values[key] = 'min'
                elif current_value == "max":
                    default_values[key] = 'max'
                elif current_value == 'default':
                    if type == 'embedding':
                        default_values[key] = config_items[key]['default']
                    else:
                        default_values[key] = 'default'
                else:
                    if key in config_items:
                        if key == 'model':
                            default_values[key] = value.get('default', None)
                            continue
                        if key == 'response_type':
                            current_type = current_value.get('type') if isinstance(current_value, dict) else None
                            if current_type and any(opt.get('type') == current_type for opt in config_items[key]['options']):
                                default_values[key] = current_value
                                if current_type == 'json_schema':
                                    default_values['response_type']['json_schema'] = current_value.get('json_schema', None)
                            else:
                                default_values[key] = value.get('default', None)
                            continue    
                        min_value = value.get('min')
                        max_value = value.get('max')
                        if min_value is not None and max_value is not None:
                            if current_value is not None and not (min_value <= current_value <= max_value):
                                default_values[key] = value.get('default', None)
                            else:
                                if current_value is None:
                                    default_values[key] = 'default'
                                else:
                                    default_values[key] = current_value
                        else:
                            if current_value is None:
                                default_values[key] = 'default'
                            else:
                                default_values[key] = current_value
                    else:
                        default_values[key] = value.get('default', None) if key == 'model' or type == 'embedding' else 'default'
            
            return default_values

        modelObj = model_config_document[service][model]

        if modelObj is None:
            raise HTTPException(status_code=400, detail=f"Invalid model: {model}")

        if service == service_name['openai']:
            return get_default_values(modelObj)
            
        elif service == service_name['anthropic']:
            return get_default_values(modelObj)
        
        elif service == service_name['groq']:
            return get_default_values(modelObj)
        
        elif service == service_name['openai_response']:
            return get_default_values(modelObj)
        
        elif service == service_name['open_router']:
            return get_default_values(modelObj)
        
        elif service == service_name['mistral']:
            return get_default_values(modelObj)
        
        else:
            raise HTTPException(status_code=404, detail=f"Service '{service}' not found.")
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
