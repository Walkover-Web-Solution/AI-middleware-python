from fastapi import Request, HTTPException
from ..services.utils.getConfiguration import getConfiguration
from globals import *
from src.configs.model_configuration import model_config_document

async def add_configuration_data_to_body(request: Request):

    try:
        body = await request.json()
        chatbotData = getattr(request.state, "chatbot", None)
        if chatbotData:
            body.update(chatbotData)
        bridge_id = body.get('agent_id') or body.get("bridge_id") or request.path_params.get('bridge_id') or getattr(request.state, 'chatbot', {}).get('bridge_id', None)
        if chatbotData:
            del request.state.chatbot
        version_id = body.get('version_id') or request.path_params.get('version_id')
        db_config = await getConfiguration(body.get('configuration'), body.get('service'), bridge_id, body.get('apikey'), body.get('template_id'), body.get('variables', {}), request.state.profile.get("org",{}).get("id",""), body.get('variables_path'), version_id = version_id, extra_tools = body.get('extra_tools',[]), built_in_tools = body.get('built_in_tools'))
        if not db_config.get("success"):
                raise HTTPException(status_code=400, detail={"success": False, "error": db_config["error"]}) 
        body.update(db_config)
        service = body.get("service")
        model = body.get("configuration").get('model')
        user = body.get("user")
        images = body.get("images") or []
        if user is None and len(images) == 0:
            raise HTTPException(status_code=400, detail={"success": False, "error": "User message is compulsory"})
        if not (service in model_config_document and model in model_config_document[service]):
            raise HTTPException(status_code=400, detail={"success": False, "error": "model or service does not exist!"})
        return db_config
    except HTTPException as he:
         raise he
    except Exception as e:
        logger.error(f"Error in get_data: {str(e)}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in getting data: "+ str(e)})
    

