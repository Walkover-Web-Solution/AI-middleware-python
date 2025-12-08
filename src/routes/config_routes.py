from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.configController import create_bridges_controller, get_bridge as get_bridge_controller,  get_all_bridges as get_all_bridges_controller, create_bridges_using_ai_controller
from ..controllers.configController import get_all_service_models_controller,update_bridge_controller, get_all_service_controller, get_all_in_built_tools_controller, get_bridges_and_versions_by_model_controller, clone_agent_controller, invite_user_controller
from src.controllers.apicallControllerV2 import creates_api, updates_api
router = APIRouter()

@router.get('/service/models/{service}',dependencies=[Depends(jwt_middleware)])
async def get_all_service_models(service: str, request: Request):
    return await get_all_service_models_controller(service, request)

@router.get('/service',dependencies=[Depends(jwt_middleware)])
async def get_all_service():
    return await get_all_service_controller()

@router.get('/getbridges/all',dependencies=[Depends(jwt_middleware)])
async def get_all_bridges(request: Request):
    return await get_all_bridges_controller(request)

@router.get('/getbridges/{bridge_id}',dependencies=[Depends(jwt_middleware)])
async def get_bridge(request: Request,bridge_id: str):
    return await get_bridge_controller(request,bridge_id)

@router.post('/create_bridge',dependencies=[Depends(jwt_middleware)])
async def create_bridge(request: Request):
    return await create_bridges_controller(request)

@router.post('/create_bridge_using_ai',dependencies=[Depends(jwt_middleware)])
async def create_bridge(request: Request):
    return await create_bridges_using_ai_controller(request)

@router.post('/update_bridge/{bridge_id}',dependencies=[Depends(jwt_middleware)])
async def update_bridge(request: Request,bridge_id: str):
    return await update_bridge_controller(request,bridge_id = bridge_id)

@router.post('/createapi', dependencies=[Depends(jwt_middleware)])
async def create_api(request: Request):
    return await creates_api(request)

@router.post('/updateapi/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def update_api(bridge_id: str, request: Request):
    return await updates_api(request, bridge_id)

@router.get('/inbuilt/tools',dependencies=[Depends(jwt_middleware)])
async def get_all_tools():
    return await get_all_in_built_tools_controller()

@router.get('/getBridgesAndVersions/{model_name}')
async def get_bridges_and_versions_by_model(model_name: str):
    return await get_bridges_and_versions_by_model_controller(model_name)

@router.post('/clone_agent', dependencies=[Depends(jwt_middleware)])
async def clone_agent(request: Request):
    return await clone_agent_controller(request)

@router.post('/invite_user/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def invite_user(request: Request, bridge_id: str):
    return await invite_user_controller(request, bridge_id)
