from fastapi import APIRouter, Depends, Request
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config import Config
from src.middlewares.interfaceMiddlewares import send_data_middleware, chat_bot_auth
from src.middlewares.ratelimitMiddleware import rate_limit
from src.db_services.ConfigurationServices import makeStaticData
router = APIRouter()
executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)
from ..middlewares.middleware import jwt_middleware

async def auth_and_rate_limit(request: Request):
    await chat_bot_auth(request)
    await rate_limit(request, key_path='profile.userId')

@router.post("/{botId}/sendMessage", dependencies=[Depends(auth_and_rate_limit)])
async def send_message(request: Request, botId: str):
   # Get the current event loop
   loop = asyncio.get_event_loop()

    # Run the async function in a separate thread to avoid blocking
   result = await loop.run_in_executor(executor, lambda: asyncio.run(send_data_middleware(request, botId)))
   return result

@router.get("/{bridge_id}/staticResponseSave", dependencies=[Depends(jwt_middleware)])
async def static_response_save(bridge_id: str):
    return await makeStaticData(bridge_id)
