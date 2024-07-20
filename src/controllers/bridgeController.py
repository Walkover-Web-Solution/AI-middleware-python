from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
import asyncio
from ..middlewares.middleware import jwt_middleware
import traceback
from src.db_services.ConfigurationServices import get_bridges

router = APIRouter()

@router.post('/chat/completion', dependencies=[Depends(jwt_middleware)])
async def duplicate_bridge(request: Request):
    try:
        bridge_id = request. 
        bridges_data = await get_bridges()
        return JSONResponse(content={"data": bridges_data}, status_code=200)
    except Exception as e:
        # Log the exception with traceback for debugging purposes
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)
