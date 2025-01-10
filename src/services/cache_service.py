import json
from typing import Union, List, Iterable
from config import Config
from redis.asyncio import Redis
from fastapi.responses import JSONResponse
import logging

# Initialize the Redis client
client = Redis.from_url(Config.REDIS_URI)  # Adjust these parameters as needed

REDIS_PREFIX = 'AIMIDDLEWARE_'
DEFAULT_REDIS_TTL = 172800  # 2 days

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def store_in_cache(identifier: str, data: dict, ttl: int = DEFAULT_REDIS_TTL) -> bool:
    try:
        # Convert ttl to int in case it's passed as a string
        ttl = int(ttl)
        success = await client.set(f"{REDIS_PREFIX}{identifier}", json.dumps(data), ex=ttl)
        if success:
            logger.info(f"Data for {identifier} stored successfully in Redis")
        return success
    except Exception as e:
        logger.error(f"Error storing in cache for {identifier}: {e}")
        return False

async def find_in_cache(identifier: str) -> Union[str, None]:
    try:
        cached_data = await client.get(f"{REDIS_PREFIX}{identifier}")
        if cached_data:
            return cached_data.decode()  # Decode to get the string
        return None
    except Exception as e:
        logger.error(f"Error finding in cache for {identifier}: {e}")
        return None

async def delete_in_cache(identifiers: Union[str, List[str]]) -> bool:
    try:
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        
        # Create a list of keys to delete
        keys_to_delete = [f"{REDIS_PREFIX}{id}" for id in identifiers]
        delete_count = await client.delete(*keys_to_delete)
        
        logger.info(f"Deleted {delete_count} items from cache")
        return delete_count > 0
    except Exception as e:
        logger.error(f"Error during deletion of {identifiers}: {e}")
        return False

async def verify_ttl(identifier: str) -> int:
    try:
        key = f"{REDIS_PREFIX}{identifier}"
        ttl = await client.ttl(key)
        if ttl == -1:
            logger.info(f"Key {key} exists but has no TTL set")
        elif ttl == -2:
            logger.info(f"Key {key} does not exist")
        else:
            logger.info(f"TTL for key {key} is {ttl} seconds")
        return ttl
    except Exception as e:
        logger.error(f"Error retrieving TTL for key {identifier}: {e}")
        return -1  # Indicating error

async def clear_cache(request) -> JSONResponse:
    try:
        body = await request.json()
        id = body.get('id')
        if id:
            success = await delete_in_cache(id)
            if success:
                return JSONResponse(status_code=200, content={"message": "Redis Key cleared successfully"})
            return JSONResponse(status_code=400, content={"message": "Error deleting the key"})
        
        # If no specific id, clear all keys with the prefix
        cursor = b'0'
        while cursor:
            cursor, keys = await client.scan(cursor=cursor, match=f"{REDIS_PREFIX}*")
            if keys:
                await client.delete(*keys)
        logger.info("Cleared all items with prefix from cache")
        return JSONResponse(status_code=200, content={"message": "Redis cleared successfully"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return JSONResponse(status_code=400, content={"message": f"Error clearing cache: {e}"})

__all__ = ['delete_in_cache', 'store_in_cache', 'find_in_cache', 'verify_ttl', 'clear_cache']
