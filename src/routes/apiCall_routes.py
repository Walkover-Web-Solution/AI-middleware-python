from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.apiCallController import get_all_apicalls_controller
from ..controllers.apiCallController import update_apicalls_controller
from fastapi.responses import JSONResponse
router = APIRouter()

@router.get('/all', dependencies=[Depends(jwt_middleware)])
async def get_all_apicalls(request: Request):
    return await get_all_apicalls_controller(request)

@router.put('/{function_id}', dependencies=[Depends(jwt_middleware)])
async def update_apicalls(request: Request, function_id: str):
    return await update_apicalls_controller(request, function_id)

@router.get('/test', dependencies=[Depends(jwt_middleware)])
async def get_all_apicalls(request: Request):
    return  JSONResponse(status_code=200, content={
                "success": True,
                "message": "Sucessfully authenticated",
                "org_id": request.state.profile['org']['id'],
                "organization_name":  request.state.profile['org']['name'],
            })