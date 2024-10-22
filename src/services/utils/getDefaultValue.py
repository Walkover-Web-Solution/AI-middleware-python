from src.configs.modelConfiguration import ModelsConfig as model_configuration
from ...configs.constant import service_name
from fastapi import HTTPException

async def get_default_values_controller(service, model, current_configuration: dict):
    try:
        service = service.lower()
        
        def get_default_values(config):
            default_values = {}
            config_items = config.get('configuration', {})
            
            for key, value in config_items.items():
                if(key=='type'):
                    continue
                if current_configuration.get(key) == "min":
                    default_values[key] = 'min' 
                elif current_configuration.get(key) == "max":
                    default_values[key] = 'max'
                elif current_configuration.get(key) == 'default':
                    default_values[key] = 'default'
                else:
                    default_values[key] = value.get('default', None)
            
            return default_values

        modelname = model.replace("-", "_").replace(".", "_")    
        configuration = getattr(model_configuration, modelname, None)

        if configuration is None:
            raise HTTPException(status_code=400, detail=f"Invalid model: {model}")

        if service == service_name['openai']:
            return get_default_values(configuration())
            
        elif service == service_name['anthropic']:
            return get_default_values(configuration())
        
        elif service == service_name['groq']:
            return get_default_values(configuration())
        
        else:
            raise HTTPException(status_code=404, detail=f"Service '{service}' not found.")
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
