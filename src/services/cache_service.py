import json
from typing import Union, List
from config import Config
from redis.asyncio import Redis

# Initialize the Redis client
client = Redis.from_url(Config.REDIS_URI)  # Adjust these parameters as needed

REDIS_PREFIX = 'AIMIDDLEWARE_'
DEFAULT_REDIS_TTL = 172800  # 2 days

async def store_in_cache(identifier: str, data: dict, ttl: int = DEFAULT_REDIS_TTL) -> bool:
    try:
        return await client.set(f"{REDIS_PREFIX}{identifier}", json.dumps(data), ex=int(ttl))
    except Exception as e:
        print(f"Error storing in cache: {e}")
        return False

async def find_in_cache(identifier: str) -> Union[str, None]:
    try:
        return await client.get(f"{REDIS_PREFIX}{identifier}")
    except Exception as e:
        print(f"Error finding in cache: {e}")
        return None

async def delete_in_cache(identifiers: Union[str, List[str]]) -> bool:
    if not client.ping():
        return False
    
    if isinstance(identifiers, str):
        identifiers = [identifiers]
    
    keys_to_delete = [f"{REDIS_PREFIX}{id}" for id in identifiers]

    try:
        delete_count = await client.delete(*keys_to_delete)
        print(f"Deleted {delete_count} items from cache")
        return True
    except Exception as error:
        print(f"Error during deletion: {error}")
        return False

async def verify_ttl(identifier: str) -> int:
    try:
        if client.ping():
            key = f"{REDIS_PREFIX}{identifier}"
            ttl = await client.ttl(key)
            print(f"TTL for key {key} is {ttl} seconds")
            return ttl
        else:
            print("Redis client is not ready")
            return -2  # Indicating error
    except Exception as error:
        print(f"Error retrieving TTL from cache: {error}")
        return -1  # Indicating error

__all__ = ['delete_in_cache', 'store_in_cache', 'find_in_cache', 'verify_ttl']