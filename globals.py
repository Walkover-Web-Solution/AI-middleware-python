from src.services.utils.logger import logger
from exceptions.bad_request import BadRequestException
import traceback
import asyncio


async def try_catch(fn, *args, **kwargs):
    try:
        return await fn(*args, **kwargs)
    except Exception as e:
        return None


REDIS_SEMAPHORE = asyncio.Semaphore(200)
MONGO_SEMAPHORE = asyncio.Semaphore(50)

__all__ = ['logger', 'BadRequestException', 'traceback', 'try_catch', 'REDIS_SEMAPHORE', 'MONGO_SEMAPHORE']
