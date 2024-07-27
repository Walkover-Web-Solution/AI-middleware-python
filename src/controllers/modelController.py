from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from ..services.utils.getConfiguration import getConfiguration
import asyncio
from src.services.commonServices.common import (
   chat,
    #, proCompletion, getCompletion, proEmbeddings, getEmbeddings
)
from ..middlewares.middleware import jwt_middleware
from ..middlewares.getDataUsingBridgeId import get_data
import traceback
router = APIRouter()

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request,db_config: dict = Depends(get_data)):
    try:
        body = await request.json()
        db_config['RTLayer'] = body.get('RTLayer') or db_config.get('RTLayer')
        request.state.playground = False
        if(body.get('webhook') or body.get('RTLayer')):
            asyncio.create_task(chat(request))
            return JSONResponse(status_code=200, content={"success": True, "message"  :"Your response will be send through configured means."}) 
        return await chat(request)
    except Exception as e:
        print("Error in chat completion: ", e)
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": "Error in chat completion: "+str(e)})

@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(bridge_id: str, request: Request,db_config: dict = Depends(get_data)):
    request.state.playground = True
    return await chat(request)
