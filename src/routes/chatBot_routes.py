from fastapi import APIRouter, Depends, Request
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.middlewares.interfaceMiddlewares import send_data_middleware,chat_bot_auth
from src.services.commonServices import common
router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)

@router.post("/{botId}/sendMessage", dependencies=[Depends(chat_bot_auth)])
async def send_message(request: Request, botId: str):
   # Get the current event loop
   loop = asyncio.get_event_loop()

    # Run the async function in a separate thread to avoid blocking
   result = await loop.run_in_executor(executor, lambda: asyncio.run(send_data_middleware(request, botId)))
   return result