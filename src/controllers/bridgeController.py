from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
import traceback
from src.services.commonServices.bridgeServices import duplicate_bridge
router = APIRouter()

@router.post('/duplicate',dependencies=[Depends(jwt_middleware)])
async def duplicate_bridges(request: Request):
    return await duplicate_bridge(request)