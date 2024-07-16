from fastapi import APIRouter, Depends, Request

from src.middlewares.interfaceMiddlewares import send_data_middleware,chat_bot_auth
from src.db_services.ConfigurationServices import makeStaticData
from src.services.commonServices import common
router = APIRouter()

@router.post("/{botId}/sendMessage", dependencies=[Depends(chat_bot_auth)])
async def send_message(request: Request, botId: str):
   return await send_data_middleware(request, botId)

@router.get("/{bridge_id}/staticResponseSave", dependencies=[Depends(chat_bot_auth)])
async def static_response_save(bridge_id: str):
    return await makeStaticData(bridge_id)
