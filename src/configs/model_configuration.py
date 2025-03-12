from src.services.utils.load_model_configs import get_model_configurations

model_config_document = {}

async def init_model_configuration():
    global model_config_document
    new_document = await get_model_configurations()
    model_config_document.update(new_document)
    