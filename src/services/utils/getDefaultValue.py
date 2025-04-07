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
            
                if current_configuration.get(key) == "min":
                    default_values[key] = 'min' 
                elif current_configuration.get(key) == "max":
                    default_values[key] = 'max'
                elif current_configuration.get(key) == 'default':
                    if type == 'embedding':
                        default_values[key] = config_items[key]['default']
                    else:
                        default_values[key] = 'default'
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
        
        else:
            raise HTTPException(status_code=404, detail=f"Service '{service}' not found.")
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
