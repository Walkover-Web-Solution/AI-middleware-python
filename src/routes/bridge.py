from fastapi import APIRouter, Depends, Request

from src.middlewares.interfaceMiddlewares import send_data_middleware,chat_bot_auth
from src.services.commonServices import common
router = APIRouter()

@router.post("/duplicateBridge/sendMessage", dependencies=[Depends()])
async def send_message(request: Request, botId: str):
   return await duplicate_bridge(request, botId)