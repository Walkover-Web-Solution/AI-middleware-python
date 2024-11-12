from fastapi import Request
from fastapi.responses import JSONResponse
from functools import wraps
import traceback
import sys
import json
from src.services.utils.send_error_webhook import send_error_to_webhook
import asyncio

def handle_exceptions(func):
    @wraps(func)
    async def wrapper(request_body, *args, **kwargs):
        try:
            body = request_body.get('body', {})
            if 'state' in request_body and 'body' in request_body['state']:
                body.update(request_body['state']['body'])
            request_body['state']['body'] = body
            request_body['state']['body']['execution_time_logs'] = {}
            return await func(request_body, *args, **kwargs)
        
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            path_params = request_body['path_params']
            state = request_body['state']
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
                    "error_message": error_details
                }
            bridge_id = path_params.get('bridge_id') or body.get("bridge_id")
            org_id = state['profile']['org']['id']
            await send_error_to_webhook(bridge_id, org_id,error_json, type = 'Error')
            return JSONResponse(
                status_code=400,
                content=json.loads(json.dumps({
                    "success": False,
                    "error": exc.args[0] if isinstance(exc, ValueError) and isinstance(exc.args[0], dict) else str(exc),
                    "error_location": error_location,
                }))
            )
    
    return wrapper

