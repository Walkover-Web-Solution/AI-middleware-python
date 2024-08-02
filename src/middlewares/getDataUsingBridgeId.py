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
        bridge_id = body.get("bridge_id") or request.path_params.get('bridge_id')
        db_config = await getConfiguration(body.get('configuration'), body.get('service'), bridge_id, body.get('apikey'), body.get('template_id'))
        if not db_config.get("success"):
                return JSONResponse(status_code=400, content={"success": False, "error": db_config["error"]}) 
        body.update(db_config)
        response_format = body.get('configuration', {}).get("response_format")
        request.state.body = body
        service = body.get("service")
        model = body.get("configuration").get('model')
        if not (service in services and model in services[service]["chat"]):
            raise HTTPException(status_code=400, detail={"success": False, "error": "model or service does not exist!"})
        if(response_format.get('type') != 'default'):
            asyncio.create_task(chat(request))
            raise HTTPException(status_code=200, detail={"success": True, "message"  :"Your response will be send through configured means."}) 
        return db_config
    except HTTPException as he:
         raise he
    except Exception as e:
        print("Error in get_data: ", e)
        traceback.print_exc()
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in getting data: "+ str(e)})


