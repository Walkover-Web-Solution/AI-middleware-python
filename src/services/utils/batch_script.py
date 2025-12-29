from ..cache_service import find_in_cache_with_prefix, delete_in_cache
from openai import AsyncOpenAI
from ..utils.send_error_webhook import create_response_format
from ..commonServices.baseService.baseService import sendResponse
import asyncio
import json
import httpx
import certifi
from .ai_middleware_format import  Batch_Response_formatter
from src.configs.constant import redis_keys
from globals import *
import uuid
import time

async def acquire_lock(batch_id: str, ttl: int = 300) -> tuple[bool, str]:
    """
    Acquire a distributed lock for a batch_id using Redis.
    Returns (success: bool, lock_id: str)
    TTL is in seconds (default 5 minutes to handle processing time)
    """
    lock_key = f"batch_lock:{batch_id}"
    lock_id = str(uuid.uuid4())
    
    try:
        from models.mongo_connection import redis_client
        # SET NX (set if not exists) with expiration
        # This is atomic and prevents race conditions
        acquired = await asyncio.to_thread(
            redis_client.set,
            lock_key,
            lock_id,
            nx=True,  # Only set if key doesn't exist
            ex=ttl    # Expire after TTL seconds
        )
        return (bool(acquired), lock_id)
    except Exception as e:
        logger.error(f"Error acquiring lock for batch {batch_id}: {str(e)}")
        return (False, "")


async def release_lock(batch_id: str, lock_id: str) -> bool:
    """
    Release a distributed lock only if we own it (lock_id matches).
    This prevents releasing another server's lock.
    """
    lock_key = f"batch_lock:{batch_id}"
    
    try:
        from models.mongo_connection import redis_client
        
        # Lua script to atomically check and delete the lock
        # This ensures we only delete our own lock
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = await asyncio.to_thread(
            redis_client.eval,
            lua_script,
            1,  # number of keys
            lock_key,
            lock_id
        )
        return bool(result)
    except Exception as e:
        logger.error(f"Error releasing lock for batch {batch_id}: {str(e)}")
        return False


async def repeat_function():
    while True:
        await check_batch_status()
        await asyncio.sleep(900)



async def check_batch_status():
    try:
        print("Batch Script running...")
        batch_ids = await find_in_cache_with_prefix('batch_')
        if batch_ids is None:
            return
        
        for id in batch_ids:
            batch_id = id.get('id')
            
            # Try to acquire lock for this batch
            lock_acquired, lock_id = await acquire_lock(batch_id, ttl=300)
            
            if not lock_acquired:
                # Another server is already processing this batch, skip it
                logger.info(f"Batch {batch_id} is being processed by another server, skipping...")
                continue
            
            # We have the lock, process the batch
            logger.info(f"Lock acquired for batch {batch_id}, processing...")
            
            try:
                apikey = id.get('apikey')
                webhook = id.get('webhook')
                batch_variables = id.get('batch_variables')  # Retrieve batch_variables from cache
                custom_id_mapping = id.get('custom_id_mapping', {})  # Get mapping of custom_id to index
                
                if webhook.get('url') is not None:
                    response_format = create_response_format(webhook.get('url'), webhook.get('headers'))
                
                # Create httpx client with proper production configuration
                limits = httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=30.0
                )
                
                http_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(60.0, connect=10.0),
                    transport=httpx.AsyncHTTPTransport(
                        retries=3,
                        verify=certifi.where()
                    ),
                    limits=limits,
                    follow_redirects=True
                )
                
                try:
                    openAI = AsyncOpenAI(api_key=apikey, http_client=http_client)
                    batch = await openAI.batches.retrieve(batch_id)
                    if batch.status == "completed":
                        file = batch.output_file_id or batch.error_file_id
                        file_response = None
                        if file is not None:
                            file_response = await openAI.files.content(file)
                            file_content = await asyncio.to_thread(file_response.read)
                            try:
                                # Split the data by newline and parse each JSON object separately
                                file_content = [json.loads(line) for line in file_content.decode('utf-8').splitlines() if line.strip()]
                            except json.JSONDecodeError as e:
                                print(f"JSON decoding error: {e}")
                                file_content = None
                            for index, content in enumerate(file_content):
                                response = content.get("response", {})
                                response_body = response.get("body", {})
                                status_code = response.get("status_code", 200)
                                custom_id = content.get("custom_id", None)
                                
                                # Check if response contains an error (status_code >= 400 or error in body)
                                if status_code >= 400 or "error" in response_body:
                                    # Handle error response
                                    formatted_content = {
                                        "custom_id": custom_id,
                                        "batch_id": batch_id,
                                        "error": response_body.get("error", response_body),
                                        "status_code": status_code
                                    }
                                else:
                                    # Handle successful response
                                    formatted_content = await Batch_Response_formatter(response=response_body, service='openai_batch', tools={}, type='chat', images=None, batch_id=batch_id, custom_id=custom_id)
                                
                                # Add batch_variables to response if available
                                if batch_variables is not None and custom_id in custom_id_mapping:
                                    variable_index = custom_id_mapping[custom_id]
                                    if variable_index < len(batch_variables):
                                        formatted_content["variables"] = batch_variables[variable_index]
                                
                                file_content[index] = formatted_content
                            
                            # Check if all responses are errors
                            has_success = any(item.get("status_code") is None or item.get("status_code", 200) < 400 for item in file_content)
                            
                            await sendResponse(response_format, data=file_content, success=has_success)
                        
                        # Delete from cache only after successful processing
                        cache_key = f"{redis_keys['batch_']}{batch_id}"
                        await delete_in_cache(cache_key)
                        logger.info(f"Batch {batch_id} processed successfully and removed from cache")
                    else:
                        # Batch not completed yet, release lock so it can be checked again
                        logger.info(f"Batch {batch_id} status: {batch.status}, will check again later")
                finally:
                    # Ensure http_client is properly closed
                    await http_client.aclose()
            finally:
                # Always release the lock, even if an error occurred
                await release_lock(batch_id, lock_id)
                logger.info(f"Lock released for batch {batch_id}")
                
    except Exception as error:
        logger.error(f"An error occurred while checking the batch status: {str(error)}")
        
    
    