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

@router.post('/chat/completion')
async def chat_completion(request: Request):
    return JSONResponse(
        status_code=410,
        content={
            "success": False,
            "message": "This route is deprecated. Please use /api/v2/model/chat/completion instead."
        }
    )
@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    # Mark the request as coming from playground
    request.state.is_playground = True
    request.state.version = 1
    
    result = await chat(request)
    return result
