from fastapi import APIRouter, Request, Depends
from ..middlewares.middleware import jwt_middleware
from src.controllers.testcase_controller import get_testcases_history
router = APIRouter()


@router.get('/{bridge_id}', dependencies=[Depends(jwt_middleware)])
async def create_vertors(request: Request, bridge_id : str):
    """Return execution history for testcases linked to `bridge_id`."""
    return await get_testcases_history(request, bridge_id)
