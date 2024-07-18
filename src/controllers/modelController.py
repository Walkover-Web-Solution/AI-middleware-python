from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from ..services.utils.getConfiguration import getConfiguration
import asyncio
from src.services.commonServices.common import (
    prochat,
    getchat#, proCompletion, getCompletion, proEmbeddings, getEmbeddings
)
from ..middlewares.middleware import jwt_middleware
import traceback
router = APIRouter()

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request):
    try:
        body = await request.json()##
        if(hasattr(request.state, 'body')):
            body.update(request.state.body)
        db_config = await getConfiguration(body.get('configuration'), body.get('service'), body.get('bridge_id'), body.get('apikey'), body.get('template_id'))
        if not db_config.get("success"):
                return JSONResponse(status_code=400, content={"success": False, "error": db_config["error"]})
        db_config['RTLayer'] = body.get('RTLayer') or db_config.get('RTLayer')
        body.update(db_config)
        request.state.body = body
        if(body.get('webhook') or body.get('RTLayer')):
            asyncio.create_task(prochat(request))
            return JSONResponse(status_code=200, content={"success": True, "message"  :"Your response will be send through configured means."}) 
        
        return await prochat(request)
    except Exception as e:
        print("Error in chat completion: ", e)
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": "Error in chat completion: "+str(e)})

@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(bridge_id: str, request: Request):
    return await getchat(request, bridge_id)
