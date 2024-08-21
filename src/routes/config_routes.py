from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.configController import create_bridges_controller, get_bridge as get_bridge_controller,  get_all_bridges as get_all_bridges_controller
from ..controllers.configController import get_all_service_models_controller,update_bridge_controller, apikey_update_controller
from src.services.commonServices.apiCallService import creates_api, updates_api
router = APIRouter()

@router.get('/service/models/{service}',dependencies=[Depends(jwt_middleware)])
async def get_all_service_models(service: str):
    return await get_all_service_models_controller(service)

@router.get('/getbridges/all',dependencies=[Depends(jwt_middleware)])
async def get_all_bridges(request: Request):
    return await get_all_bridges_controller(request)

@router.get('/getbridges/{bridge_id}',dependencies=[Depends(jwt_middleware)])
async def get_bridge(request: Request,bridge_id: str):
    return await get_bridge_controller(request,bridge_id)

@router.post('/create_bridge',dependencies=[Depends(jwt_middleware)])
async def create_bridge(request: Request):
    return await create_bridges_controller(request)

@router.post('/update_bridge/{bridge_id}',dependencies=[Depends(jwt_middleware)])
async def update_bridge(request: Request,bridge_id: str, to_update : bridge_update_validation):
    return await update_bridge_controller(request,bridge_id)

@router.post('/createapi/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def create_api(bridge_id: str, request: Request):
    return await creates_api(request, bridge_id)

@router.post('/updateapi/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def update_api(bridge_id: str, request: Request):
    return await updates_api(request, bridge_id)

@router.post('/apikey/update', dependencies=[Depends(jwt_middleware)])
async def update_apikey(request: Request):
    return await apikey_update_controller(request)