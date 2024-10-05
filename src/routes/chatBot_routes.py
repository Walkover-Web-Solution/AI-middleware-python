from fastapi import APIRouter, Depends, Request
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config import Config
from src.middlewares.interfaceMiddlewares import send_data_middleware, chat_bot_auth, reset_chatBot
from src.middlewares.ratelimitMiddleware import rate_limit

router = APIRouter()
executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

async def auth_and_rate_limit(request: Request):
    await chat_bot_auth(request)
    await rate_limit(request, key_path='profile.user.id')

@router.post("/{botId}/sendMessage", dependencies=[Depends(auth_and_rate_limit)])
async def send_message(request: Request, botId: str):
   result = await send_data_middleware(request, botId)
   return result

@router.post("/{botId}/resetchat", dependencies=[Depends(auth_and_rate_limit)])
async def reset_chat(request: Request, botId: str):
    return await reset_chatBot(request, botId)
