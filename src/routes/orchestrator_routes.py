from fastapi import APIRouter, Request, Depends
from src.middlewares.middleware import jwt_middleware
from src.controllers.orchestratorController import (
    create_orchestrator_controller,
    get_all_orchestrators_controller,
    delete_orchestrator_controller
)

router = APIRouter()

@router.post('/', dependencies=[Depends(jwt_middleware)])
async def create_orchestrator(request: Request):
    return await create_orchestrator_controller(request)

@router.get('/all', dependencies=[Depends(jwt_middleware)])
async def get_all_orchestrators(request: Request):
    return await get_all_orchestrators_controller(request)

@router.delete('/{orchestrator_id}', dependencies=[Depends(jwt_middleware)])
async def delete_orchestrator(orchestrator_id: str, request: Request):
    return await delete_orchestrator_controller(orchestrator_id, request)
