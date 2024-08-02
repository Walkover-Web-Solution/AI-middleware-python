from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
import asyncio
from src.services.commonServices.common import chat
from ..middlewares.middleware import jwt_middleware
from ..middlewares.getDataUsingBridgeId import add_configuration_data_to_body
import traceback
router = APIRouter()

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    try:
        request.state.playground = False # yaha se remove karna hai
        return await chat(request) # confirm karna ki ui kaise bhejega playground
    except Exception as e:
        print("Error in chat completion: ", e)
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": "Error in chat completion: "+str(e)})

@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.playground = True # yaha se remove karna hai
    return await chat(request)
