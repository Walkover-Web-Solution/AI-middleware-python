from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.bridge_version_controller import create_version
router = APIRouter()
@router.post('/create/version', dependencies=[Depends(jwt_middleware)])
async def create(request: Request):
    return await create_version(request)

