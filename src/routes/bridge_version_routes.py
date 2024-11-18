from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.bridge_version_controller import create_version, get_version
from ..controllers.configController import update_bridge_controller
router = APIRouter()
@router.post('/create', dependencies=[Depends(jwt_middleware)])
async def create(request: Request):
    return await create_version(request)

@router.put('/update/{version_id}',dependencies=[Depends(jwt_middleware)])
async def update_version(request: Request,version_id: str):
    return await update_bridge_controller(request,version_id = version_id)

@router.get('/get/{version_id}',dependencies=[Depends(jwt_middleware)])
async def get_bridge(request: Request,version_id: str):
    return await get_version(request,version_id)