from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.bridge_version_controller import create_version, get_version, publish_version, discard_version, suggest_model, check_testcases, bulk_publish_version
from ..controllers.configController import update_bridge_controller
router = APIRouter()
@router.post('/create', dependencies=[Depends(jwt_middleware)])
async def create(request: Request):
    """Create a draft bridge version from the submitted configuration."""
    return await create_version(request)

@router.put('/update/{version_id}',dependencies=[Depends(jwt_middleware)])
async def update_version(request: Request,version_id: str):
    """Update the draft version identified by `version_id`."""
    return await update_bridge_controller(request,version_id = version_id)

@router.get('/get/{version_id}',dependencies=[Depends(jwt_middleware)])
async def get_bridge(request: Request,version_id: str):
    """Fetch version metadata and payload for `version_id`."""
    return await get_version(request,version_id)

@router.post('/publish/{version_id}', dependencies=[Depends(jwt_middleware)])
async def publish(request: Request,version_id: str):
    """Publish the specified bridge version to make it active."""
    return await publish_version(request, version_id)

@router.post('/discard/{version_id}',dependencies=[Depends(jwt_middleware)])
async def discard(request: Request, version_id: str):
    """Discard pending changes for the draft version."""
    return await discard_version(request, version_id)

@router.get('/testcases/{version_id}',dependencies=[Depends(jwt_middleware)])
async def testcases(request: Request, version_id: str):
    """Return testcase results linked to the given version."""
    return await check_testcases(request, version_id)
@router.get('/suggest/{version_id}', dependencies=[Depends(jwt_middleware)])
async def suggest(request: Request, version_id: str):
    """Provide suggested model options for the targeted bridge version."""
    return await suggest_model(request, version_id)

@router.post('/bulk_publish',dependencies=[Depends(jwt_middleware)])
async def Bulkpublish(request: Request):
    """Publish multiple bridge versions in one request."""
    return await bulk_publish_version(request)
