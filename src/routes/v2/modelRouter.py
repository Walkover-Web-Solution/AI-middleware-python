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

router = APIRouter()
executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

# Custom JSON encoder for ObjectId
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        return super().default(obj)

def handle_exceptions(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            # Ensure that request state and JSON body are properly handled
            body = await request.json()
            if hasattr(request.state, 'body'):
                body.update(request.state.body)
            request.state.body = body  # Make sure request.state.body is always set

            # Execute the wrapped function
            return await func(request, *args, **kwargs)
        
        except Exception as exc:
            # Extract exception information
            exc_type, exc_obj, exc_tb = sys.exc_info()
            tb = traceback.extract_tb(exc_tb)
            last_frame = tb[-1] if tb else None  # Handle cases where traceback might be empty
            error_location = f"{last_frame.filename.split('/')[-1]}:{last_frame.lineno}" if last_frame else "unknown location"
            
            # Log the error with traceback for debugging
            print(f"Error caught in {error_location}: {exc}")
            traceback.print_exc()
            
            # Handle the response format
            response_format = request.state.body.get("configuration", {}).get("response_format", {})
            if response_format.get('type') != 'default':
                return 
            
            # Return a structured JSON response
            return JSONResponse(
                status_code=500,
                content=json.loads(json.dumps({
                    "success": False,
                    "error": "An unexpected error occurred",
                    "error_details": exc.args[0] if isinstance(exc, ValueError) and isinstance(exc.args[0], dict) else str(exc),
                    "error_location": error_location,
                    "request_data": request.state.body  # Ensure the request data is returned
                }, cls=CustomJSONEncoder))  # Use custom encoder here
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