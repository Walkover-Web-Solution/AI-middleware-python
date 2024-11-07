from fastapi import APIRouter, Depends, Request, HTTPException
import asyncio
from src.services.commonServices.common import chat
from src.services.commonServices.baseService.utils import make_request_data
from ...middlewares.middleware import jwt_middleware
from ...middlewares.getDataUsingBridgeId import add_configuration_data_to_body
from concurrent.futures import ThreadPoolExecutor
from config import Config
from src.services.commonServices.queueService.queueService import queue_obj

router = APIRouter()

executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = False
    request.state.version = 2
    
    data_to_send = await make_request_data(request)
    if (data_to_send['body'].get('chatbot', False)):
        try:
            # Publish the message to the queue
            await queue_obj.publish_message(data_to_send)
            return {"success": True, "message": "Your response will be sent through configured means."}
        except Exception as e:
            # Log the error and return a meaningful error response
            print(f"Failed to publish message: {e}")
            raise HTTPException(status_code=500, detail="Failed to publish message.")
    else:
        response_format = request.state.body.get('configuration', {}).get('response_format', {})
        loop = asyncio.get_event_loop()
        if response_format is not None and response_format.get('type') != 'default':
            await loop.run_in_executor(executor, lambda: asyncio.run(chat(data_to_send)))
            return {"success": True, "message": "Your response will be sent through configured means."}
        result = await loop.run_in_executor(executor, lambda: asyncio.run(chat(data_to_send)))
        return result


@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = True
    request.state.version = 2
    
    data_to_send = await make_request_data(request)
    if (data_to_send['body'].get('chatbot', False)):
        try:
            # Publish the message to the queue
            await queue_obj.publish_message(data_to_send)
            return {"success": True, "message": "Your response will be sent through configured means."}
        except Exception as e:
            # Log the error and return a meaningful error response
            print(f"Failed to publish message: {e}")
            raise HTTPException(status_code=500, detail="Failed to publish message.")
    else:
        response_format = request.state.body.get('configuration', {}).get('response_format', {})
        loop = asyncio.get_event_loop()
        if response_format is not None and response_format.get('type') != 'default':
            await loop.run_in_executor(executor, lambda: asyncio.run(chat(data_to_send)))
            return {"success": True, "message": "Your response will be sent through configured means."}
        result = await loop.run_in_executor(executor, lambda: asyncio.run(chat(data_to_send)))
        return result