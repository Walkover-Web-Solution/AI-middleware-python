from src.services.utils.logger import logger
from exceptions.bad_request import BadRequestException
import traceback
import asyncio

REDIS_SEMAPHORE = asyncio.Semaphore(200)
MONGO_SEMAPHORE = asyncio.Semaphore(50)

__all__ = ['logger', 'BadRequestException', 'traceback', 'REDIS_SEMAPHORE', 'MONGO_SEMAPHORE']