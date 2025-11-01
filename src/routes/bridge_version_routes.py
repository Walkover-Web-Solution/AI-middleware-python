from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from validations.validation import Bridge_update as bridge_update_validation
from ..controllers.bridge_version_controller import create_version, get_version, publish_version, discard_version, suggest_model, check_testcases, bulk_publish_version, remove_version
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

@router.post('/publish/{version_id}', dependencies=[Depends(jwt_middleware)])
async def publish(request: Request,version_id: str):
    return await publish_version(request, version_id)

@router.delete('/{version_id}', dependencies=[Depends(jwt_middleware)])
async def delete_version(request: Request, version_id: str):
    return await remove_version(request, version_id)

@router.post('/discard/{version_id}',dependencies=[Depends(jwt_middleware)])
async def discard(request: Request, version_id: str):
    return await discard_version(request, version_id)

@router.get('/testcases/{version_id}',dependencies=[Depends(jwt_middleware)])
async def testcases(request: Request, version_id: str):
    return await check_testcases(request, version_id)
@router.get('/suggest/{version_id}', dependencies=[Depends(jwt_middleware)])
async def suggest(request: Request, version_id: str):
    return await suggest_model(request, version_id)

@router.post('/bulk_publish',dependencies=[Depends(jwt_middleware)])
async def Bulkpublish(request: Request):
    return await bulk_publish_version(request)
