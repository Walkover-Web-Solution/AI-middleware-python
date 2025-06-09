import json
import asyncio
from typing import Union, List
from config import Config
from redis.asyncio import Redis
from fastapi.responses import JSONResponse
from globals import *

# Initialize the Redis client
client = Redis.from_url(Config.REDIS_URI)  # Adjust these parameters as needed

# Configure Redis to enable keyspace notifications
async def enable_notifications():
    await client.config_set('notify-keyspace-events', 'Ex')

# Function to handle expired keys
async def handle_expired_key(key: str):
    print(f"Key expired: {key}")
    # Get the value from the reference key
    ref_key = f"{key}_ref"
    value = await client.get(ref_key)
    if value:
        value_array = json.loads(value)
        print(f"Retrieved value for expired key: {value_array}")
        # Delete the reference key after processing
        await client.delete(ref_key)
        # Here you would process the value array
        # For example: await delete_files_from_cloud(value_array)

# Function to listen for expired keys
async def listen_for_expired_keys():
    try:
        pubsub = client.pubsub()
        await pubsub.subscribe('__keyevent@0__:expired')
        
        print("Started listening for key expirations...")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                print(f"Received expiration message: {message}")
                await handle_expired_key(message['data'].decode())
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Error in key expiration listener: {e}")

# Function to demonstrate key expiration (POC)
async def demo_key_expiration(key: str, value: any, ttl: int = 60):
    """Set a key with TTL and start listening for its expiration
    
    Args:
        key (str): Key to store
        value (str): Value to store
        ttl (int): Time to live in seconds (default 60 seconds)
    """
    try:
        # Enable notifications if not already enabled
        await enable_notifications()
        
        # Store the main key with TTL
        await client.set(key, 'trigger', ex=ttl)
        
        # Store the actual value in a reference key without TTL
        ref_key = f"{key}_ref"
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        await client.set(ref_key, value)
        print(f"Stored key '{key}' with TTL of {ttl} seconds")
        
        # Start listening for expired keys in the background
        asyncio.create_task(listen_for_expired_keys())
        
    except Exception as e:
        print(f"Error in demo_key_expiration: {e}")

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

__all__ = ['delete_in_cache', 'store_in_cache', 'find_in_cache', 'verify_ttl', 'clear_cache','store_in_cache_for_batch', 'find_in_cache_for_batch', 'delete_in_cache_for_batch', 'demo_key_expiration']