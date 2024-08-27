from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.apiCallController import get_all_apicalls_controller
router = APIRouter()

@router.get('/all', dependencies=[Depends(jwt_middleware)])
async def get_all_apicalls(request: Request):
    return await get_all_apicalls_controller(request)