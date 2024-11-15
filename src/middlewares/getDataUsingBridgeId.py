from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..services.utils.getConfiguration import getConfiguration
from src.configs.models import services
from src.services.commonServices.common import chat
import asyncio
import traceback
async def add_configuration_data_to_body(request: Request):

    try:
        body = await request.json()
        chatbotData = getattr(request.state, "chatbot", None)
        if chatbotData:
            body.update(chatbotData)
        bridge_id = body.get("bridge_id") or request.path_params.get('bridge_id') or getattr(request.state, 'chatbot', {}).get('bridge_id', None)
        if chatbotData:
            del request.state.chatbot
        db_config = await getConfiguration(body.get('configuration'), body.get('service'), bridge_id, body.get('apikey'), body.get('template_id'), body.get('variables', {}), request.state.profile.get("org",{}).get("id",""), body.get('variables_path'))
        if not db_config.get("success"):
                raise HTTPException(status_code=400, detail={"success": False, "error": db_config["error"]}) 
        body.update(db_config)
        # request.state.body = body
        service = body.get("service")
        model = body.get("configuration").get('model')
        if not (service in services and model in services[service]["chat"]):
            raise HTTPException(status_code=400, detail={"success": False, "error": "model or service does not exist!"})
        return db_config
    except HTTPException as he:
         raise he
    except Exception as e:
        print("Error in get_data: ", e)
        traceback.print_exc()
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in getting data: "+ str(e)})


