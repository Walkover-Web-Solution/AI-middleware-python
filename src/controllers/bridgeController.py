from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from src.services.commonServices.bridgeServices import duplicate_bridge, optimize_prompt_controller
router = APIRouter()

@router.post('/duplicate',dependencies=[Depends(jwt_middleware)])
async def duplicate_bridges(request: Request):
    return await duplicate_bridge(request)


@router.get('/{bridge_id}/optimize/prompt', dependencies=[Depends(jwt_middleware)])
async def update_apicalls(request: Request, bridge_id: str):
    return await optimize_prompt_controller(request, bridge_id)