from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from src.services.commonServices.common import chat
from ...middlewares.middleware import jwt_middleware
from ...middlewares.getDataUsingBridgeId import add_configuration_data_to_body
import traceback
import sys
from concurrent.futures import ThreadPoolExecutor
from config import Config
from functools import wraps
from bson import ObjectId
import json
from ...services.utils.send_error_webhook import send_error_to_webhook

router = APIRouter()
executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

def handle_exceptions(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            body = await request.json()
            if hasattr(request.state, 'body'):
                body.update(request.state.body)
            request.state.body = body
            return await func(request, *args, **kwargs)
        
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            tb = traceback.extract_tb(exc_tb)
            last_frame = tb[-1] if tb else None
            error_location = f"{last_frame.filename.split('/')[-1]}:{last_frame.lineno}" if last_frame else "unknown location"
            
            if isinstance(exc, ValueError):
                error_details = exc.args[0] if exc.args else str(exc)
            else:
                error_details = str(exc)

            if isinstance(error_details, ValueError):
                error_details = error_details.args[0] if error_details.args else str(error_details)

            try:
                error_json = json.loads(error_details)
            except json.JSONDecodeError:
                error_json = {
                    "location": error_location,
                    "error_message": error_details
                }
            bridge_id = request.path_params.get('bridge_id') or body.get("bridge_id")
            org_id = request.state.org_id
            asyncio.create_task(send_error_to_webhook(bridge_id, org_id,error_json, type = 'Error'))
            return JSONResponse(
                status_code=400,
                content=json.loads(json.dumps({
                    "success": False,
                    "error": exc.args[0] if isinstance(exc, ValueError) and isinstance(exc.args[0], dict) else str(exc),
                    "error_location": error_location,
                }))
            )
    
    return wrapper

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
@handle_exceptions
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = False
    request.state.version = 2
    response_format = request.state.body.get('configuration', {}).get('response_format', {})
    if response_format is not None and response_format.get('type') != 'default':
        asyncio.create_task(chat(request))
        return {"success": True, "message": "Your response will be sent through configured means."}
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, lambda: asyncio.run(chat(request)))
    return result

@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
@handle_exceptions
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = True
    request.state.version = 2

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, lambda: asyncio.run(chat(request)))
    return result