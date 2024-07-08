from fastapi import APIRouter, Depends, Request

from src.middlewares.interfaceMiddlewares import send_data_middleware
from src.services.commonServices import common
router = APIRouter()

@router.post("/{botId}/sendMessage")
async def send_message(request: Request, body: Body, botId: str = Depends(common.prochat)):
    await send_data_middleware(request, body, profile, botId)