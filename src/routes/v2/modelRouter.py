from fastapi import APIRouter, Depends, Request, HTTPException
import asyncio
from src.services.commonServices.common import chat, embedding
from src.services.commonServices.baseService.utils import make_request_data
from ...middlewares.middleware import jwt_middleware
from ...middlewares.getDataUsingBridgeId import add_configuration_data_to_body
from concurrent.futures import ThreadPoolExecutor
from config import Config
from src.services.commonServices.queueService.queueService import queue_obj
from src.middlewares.ratelimitMiddleware import rate_limit

router = APIRouter()

executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

async def auth_and_rate_limit(request: Request):
    await jwt_middleware(request)
    await rate_limit(request,key_path='body.bridge_id' , points=100)
    await rate_limit(request,key_path='body.thread_id', points=20)

@router.post('/chat/completion', dependencies=[Depends(auth_and_rate_limit)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = False
    request.state.version = 2
    data_to_send = await make_request_data(request)
    response_format = data_to_send.get('body',{}).get('configuration', {}).get('response_format', {})
    if response_format.get('type') != 'default':
        try:
            # Publish the message to the queue
            await queue_obj.publish_message(data_to_send)
            return {"success": True, "message": "Your response will be sent through configured means."}
        except Exception as e:
            # Log the error and return a meaningful error response
            print(f"Failed to publish message: {e}")
            raise HTTPException(status_code=500, detail="Failed to publish message.")
    else:
        # Assuming chat is an async function that could be blocking
        type = data_to_send.get("body",{}).get('configuration',{}).get('type')
        if type == 'embedding':
            result =  await embedding(data_to_send)
            return result
        result = await chat(data_to_send)
        return result


@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(auth_and_rate_limit)])
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = True
    request.state.version = 2
    data_to_send = await make_request_data(request)
    type = data_to_send.get("body",{}).get('configuration',{}).get('type')
    if type == 'embedding':
            result =  await embedding(data_to_send)
            return result
    result = await chat(data_to_send)
    return result