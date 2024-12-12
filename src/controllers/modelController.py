from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from src.services.commonServices.common import chat
from src.services.commonServices.baseService.utils import make_request_data
from src.services.commonServices.queueService.queueService import queue_obj
from ..middlewares.middleware import jwt_middleware
from ..middlewares.getDataUsingBridgeId import add_configuration_data_to_body
import traceback
from concurrent.futures import ThreadPoolExecutor
from config import Config
router = APIRouter()
executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    try:
        request.state.is_playground = False
        request.state.version = 1
        data_to_send = await make_request_data(request)
        response_format = data_to_send.get('body',{}).get('configuration', {}).get('response_format', {})

        if response_format.get('type') != 'default':
            try:
                # Publish the message to the queue
                await queue_obj.publish_message(data_to_send)
                return {"success": True, "message": "Your response will be sent through configured means."}
            except Exception as e:
                print(f"Failed to publish message: {e}")
                raise HTTPException(status_code=500, detail="Failed to publish message.")
        else:
            result = await chat(request)
            return result

    except Exception as e:
        print("Error in chat completion:", e)
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": "Error in chat completion: " + str(e)})

@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    # Mark the request as coming from playground
    request.state.is_playground = True
    request.state.version = 1
    
    result = await chat(request)
    return result
