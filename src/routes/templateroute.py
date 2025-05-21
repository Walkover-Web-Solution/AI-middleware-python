from fastapi import APIRouter, Request, Depends
from ..middlewares.middleware import jwt_middleware
from src.controllers.template_controller import return_template
router = APIRouter()

@router.get('/{template_id}', dependencies=[Depends(jwt_middleware)])
async def get_template(request: Request, template_id: str):
    # Process template_id here if needed
    return await return_template(request, template_id)