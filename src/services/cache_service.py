import json
from typing import Union, List
from config import Config
from redis.asyncio import Redis
from fastapi.responses import JSONResponse
from globals import *

# Initialize the Redis client
client = Redis.from_url(Config.REDIS_URI)  # Adjust these parameters as needed

REDIS_PREFIX = 'AIMIDDLEWARE_'
DEFAULT_REDIS_TTL = 172800  # 2 days

async def store_in_cache(identifier: str, data: dict, ttl: int = DEFAULT_REDIS_TTL) -> bool:
    try:
        serialized_data = make_json_serializable(data)
        return await client.set(f"{REDIS_PREFIX}{identifier}", json.dumps(serialized_data), ex=int(ttl))
    except Exception as e:
        logger.error(f"Error storing in cache: {str(e)}")
        return False

async def find_in_cache(identifier: str) -> Union[str, None]:
    try:
        return await client.get(f"{REDIS_PREFIX}{identifier}")
    except Exception as e:
        logger.error(f"Error finding in cache: {str(e)}")
        return None
        
async def find_in_cache_and_expire(identifier: str) -> Union[str, None]:
    """Find a value in cache and delete it immediately after reading (expire on read).
    
    This function implements the 'expire on read' pattern where a cached value is
    retrieved once and then immediately deleted from the cache.
    
    Args:
        identifier: The key to look up in the cache
        
    Returns:
        The cached value if found, None otherwise
    """
    try:
        key = f"{REDIS_PREFIX}{identifier}"
        # Use a pipeline to ensure atomicity of the get and delete operations
        pipe = client.pipeline()
        await pipe.get(key)
        await pipe.delete(key)
        results = await pipe.execute()
        return results[0]  # First result is from the GET operation
    except Exception as e:
        logger.error(f"Error in find_in_cache_and_expire: {str(e)}")
        return None
        
async def store_in_cache_permanent_until_read(identifier: str, data: dict) -> bool:
    """Store data in cache with no expiration time, to be retrieved only once.
    
    This function stores data in Redis with no expiration time (permanent storage).
    The data will remain in Redis indefinitely until it's read using find_in_cache_and_expire.
    
    Args:
        identifier: The key to store the data under
        data: The data to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        serialized_data = make_json_serializable(data)
        # Store without expiration time (no ex parameter)
        return await client.set(f"{REDIS_PREFIX}{identifier}", json.dumps(serialized_data))
    except Exception as e:
        logger.error(f"Error storing in permanent cache: {str(e)}")
        return False

async def delete_in_cache(identifiers: Union[str, List[str]]) -> bool:
    if not await client.ping():
        return False
    
    if isinstance(identifiers, str):
        identifiers = [identifiers]
    
    keys_to_delete = [f"{REDIS_PREFIX}{id}" for id in identifiers]

    try:
        delete_count = await client.delete(*keys_to_delete)
        print(f"Deleted {delete_count} items from cache")
        return True
    except Exception as error:
        logger.error(f"Error during deletion: {str(error)}")
        return False

async def verify_ttl(identifier: str) -> int:
    try:
        if await client.ping():
            key = f"{REDIS_PREFIX}{identifier}"
            ttl = await client.ttl(key)
            print(f"TTL for key {key} is {ttl} seconds")
            return ttl
        else:
            print("Redis client is not ready")
            return -2  # Indicating error
    except Exception as error:
        logger.error(f"Error retrieving TTL from cache: {str(error)}")
        return -1  # Indicating error

async def clear_cache(request) -> JSONResponse:
    try:
        body = await request.json()
        id = body.get('id')
        if id:
            await delete_in_cache(id)
            return JSONResponse(status_code=200, content={"message": "Redis Key cleared successfully"})
        elif await client.ping():
            # Scan for keys with the specific prefix
            cursor = b'0'
            while cursor:
                cursor, keys = await client.scan(cursor=cursor, match=f"{REDIS_PREFIX}*")
                if keys:
                    await client.delete(*keys)
            print("Cleared all items with prefix from cache")
            return JSONResponse(status_code=200, content={"message": "Redis cleared successfully"})
        else:
            logger.warning("Redis client is not ready")
            return JSONResponse(status_code=500, content={"message": "Redis client is not ready"})
    except Exception as error:
        logger.error(f"Error clearing cache: {str(error)}")
        return JSONResponse(status_code=500, content={"message": f"Error clearing cache: {error}"})

async def store_in_cache_for_batch(identifier: str, data: dict, ttl: int = DEFAULT_REDIS_TTL) -> bool:
    try:
        return await client.set(f"{identifier}", json.dumps(data), ex=int(ttl))
    except Exception as e:
        logger.error(f"Error storing in cache: {str(e)}")
        return False

async def find_in_cache_with_prefix(prefix: str) -> Union[List[str], None]:
    try:
        pattern = f"{REDIS_PREFIX}{prefix}*"
        keys = await client.keys(pattern)
        values = [json.loads(await client.get(key)) for key in keys]  # Fetch values
        return values
    
    except Exception as e:
        logger.error(f"Error finding in cache: {str(e)}")
        return None

async def delete_in_cache_for_batch(identifiers: Union[str, List[str]]) -> bool:
    if not await client.ping():
        return False
    
    if isinstance(identifiers, str):
        identifiers = [identifiers]
    
    keys_to_delete = [f"{id}" for id in identifiers]

    try:
        delete_count = await client.delete(*keys_to_delete)
        print(f"Deleted {delete_count} items from cache")
        return True
    except Exception as error:
        logger.error(f"Error during deletion: {str(error)}")
        return False
    
def make_json_serializable(data):
    """Recursively converts non-serializable values in a dictionary to strings."""
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple, set, frozenset)):
        return [make_json_serializable(v) for v in data]
    try:
        json.dumps(data)  # Check if serializable
        return data
    except (TypeError, OverflowError):
        return str(data)

__all__ = ['delete_in_cache', 'store_in_cache', 'find_in_cache', 'find_in_cache_and_expire', 'store_in_cache_permanent_until_read', 'verify_ttl', 'clear_cache','store_in_cache_for_batch', 'find_in_cache_for_batch', 'delete_in_cache_for_batch']