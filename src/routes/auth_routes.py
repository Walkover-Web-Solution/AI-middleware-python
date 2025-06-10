from fastapi import APIRouter, Request, Depends
from ..middlewares.middleware import jwt_middleware
from ..controllers.auth_controller import save_auth_token_in_db_controller, verify_auth_token_controller
router = APIRouter()


@router.post('/', dependencies=[Depends(jwt_middleware)])
async def save_auth_token_in_db(request: Request):
    return await save_auth_token_in_db_controller(request)

@router.post('/verify')
async def verify_auth_token(request: Request):
    return await verify_auth_token_controller(request)