from fastapi import APIRouter, Request, Depends
from ..middlewares.middleware import jwt_middleware
from src.controllers.testcase_controller import (
    get_testcases_history,
    create_testcase_controller,
    delete_testcase_controller,
    get_all_testcases_controller
)
router = APIRouter()


# Create a new testcase
@router.post('/create', dependencies=[Depends(jwt_middleware)])
async def create_testcase(request: Request):
    return await create_testcase_controller(request)

# Delete a testcase by _id
@router.delete('/{testcase_id}', dependencies=[Depends(jwt_middleware)])
async def delete_testcase(testcase_id: str):
    return await delete_testcase_controller(testcase_id)

# Get all testcases by bridge_id
@router.get('/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def get_all_testcases(bridge_id: str):
    return await get_all_testcases_controller(bridge_id)

# Get testcases history (existing endpoint)
@router.get('/history/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def get_testcases_history_endpoint(request: Request, bridge_id: str):
    return await get_testcases_history(request, bridge_id)