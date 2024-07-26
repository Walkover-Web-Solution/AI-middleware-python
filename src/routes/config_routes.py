from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from src.services.commonServices.apiCallService import creates_api
router = APIRouter()


@router.post('/createapi/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def create_api(bridge_id: str, request: Request):
    return await creates_api(request, bridge_id)
