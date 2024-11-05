import json
from fastapi import APIRouter, Depends, Request, FastAPI
from fastapi.responses import JSONResponse
import asyncio
from src.services.commonServices.common import chat
from src.services.commonServices.baseService.utils import make_request_data
from ...middlewares.middleware import jwt_middleware
from ...middlewares.getDataUsingBridgeId import add_configuration_data_to_body
from concurrent.futures import ThreadPoolExecutor
from config import Config
from src.services.commonServices.queueService.queueService import Queue

router = APIRouter()
queue_obj = Queue()

executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = False
    request.state.version = 2
    response_format = request.state.body.get('configuration', {}).get('response_format', {})
    loop = asyncio.get_event_loop()
    if response_format is not None and response_format.get('type') != 'default':
        await loop.run_in_executor(executor, lambda: asyncio.run(chat(request)))
        return {"success": True, "message": "Your response will be sent through configured means."}
    result = await loop.run_in_executor(executor, lambda: asyncio.run(chat(request)))
    return result


@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = True
    request.state.version = 2
    
    data_to_send = await make_request_data(request)
    await queue_obj.publish_message();
    # loop = asyncio.get_event_loop()
    # await loop.run_in_executor(None, lambda: asyncio.run(queue_obj.publish_message()))

    # result = await loop.run_in_executor(executor, lambda: asyncio.run(chat(request)))
    return True