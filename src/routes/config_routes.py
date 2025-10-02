from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.configController import create_bridges_controller, get_bridge as get_bridge_controller,  get_all_bridges as get_all_bridges_controller, create_bridges_using_ai_controller
from ..controllers.configController import get_all_service_models_controller,update_bridge_controller, get_all_service_controller, get_all_in_built_tools_controller, get_bridges_and_versions_by_model_controller
from src.controllers.apicallControllerV2 import creates_api, updates_api
router = APIRouter()

@router.get('/service/models/{service}',dependencies=[Depends(jwt_middleware)])
async def get_all_service_models(service: str, request: Request):
    """Return model metadata for the requested third-party `service`."""
    return await get_all_service_models_controller(service, request)

@router.get('/service',dependencies=[Depends(jwt_middleware)])
async def get_all_service():
    """List every provider service configured for the tenant."""
    return await get_all_service_controller()

@router.get('/getbridges/all',dependencies=[Depends(jwt_middleware)])
async def get_all_bridges(request: Request):
    """Retrieve all bridge configurations visible to the caller."""
    return await get_all_bridges_controller(request)

@router.get('/getbridges/{bridge_id}',dependencies=[Depends(jwt_middleware)])
async def get_bridge(request: Request,bridge_id: str):
    """Fetch a specific bridge definition identified by `bridge_id`."""
    return await get_bridge_controller(request,bridge_id)

@router.post('/create_bridge',dependencies=[Depends(jwt_middleware)])
async def create_bridge(request: Request):
    """Create a new bridge using the payload supplied by the authenticated user."""
    return await create_bridges_controller(request)

@router.post('/create_bridge_using_ai',dependencies=[Depends(jwt_middleware)])
async def create_bridge(request: Request):
    """Create a bridge with AI-assisted defaults based on the provided request."""
    return await create_bridges_using_ai_controller(request)

@router.post('/update_bridge/{bridge_id}',dependencies=[Depends(jwt_middleware)])
async def update_bridge(request: Request,bridge_id: str):
    """Apply updates to the bridge referenced by `bridge_id`."""
    return await update_bridge_controller(request,bridge_id = bridge_id)

@router.post('/createapi', dependencies=[Depends(jwt_middleware)])
async def create_api(request: Request):
    """Create a new API integration tied to the authenticated organisation."""
    return await creates_api(request)

@router.post('/updateapi/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def update_api(bridge_id: str, request: Request):
    """Update an existing API integration under the specified `bridge_id`."""
    return await updates_api(request, bridge_id)

@router.get('/inbuilt/tools',dependencies=[Depends(jwt_middleware)])
async def get_all_tools():
    """List tools that are bundled with the platform."""
    return await get_all_in_built_tools_controller()

@router.get('/getBridgesAndVersions/{model_name}')
async def get_bridges_and_versions_by_model(model_name: str):
    """Return bridges and associated versions available for `model_name`."""
    return await get_bridges_and_versions_by_model_controller(model_name)
