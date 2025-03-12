from src.services.utils.load_model_configs import get_model_configurations

document = {}

async def init_model_configuration():
    global document
    new_document = await get_model_configurations()
    document.update(new_document)
    