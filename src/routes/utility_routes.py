from fastapi import APIRouter, Request
from ..services.utils.formatter.ai_middleware_chat_api import structured_output_optimizer
router = APIRouter()


@router.post('/structured_output')
async def structured_output(request: Request):
    return await structured_output_optimizer(request)
