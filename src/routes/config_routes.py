from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.configController import create_bridge
router = APIRouter()

@router.post('/create_bridge',dependencies=[Depends(jwt_middleware)])
async def create_bridge(request: Request):
    body = await request.json()
    return await create_bridge(body)
