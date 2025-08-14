import asyncio
import redis.asyncio as redis
import re
from config import Config
from globals import logger
from src.db_services.ConfigurationServices import threadsModel
from src.services.cache_service import REDIS_PREFIX


async def listen_for_redis_expiration():
    """
    Listen for Redis key expiration notifications and cleanup MongoDB records.
    Only processes conversation keys with the project prefix.
    """
    redis_client = None
    pubsub = None
    
    try:
        # Setup Redis client and keyspace notifications
        redis_client = redis.Redis.from_url(Config.REDIS_URI)
        await redis_client.config_set('notify-keyspace-events', 'Ex')
        
        # Subscribe to expiration events
        pubsub = redis_client.pubsub()
        await pubsub.subscribe('__keyevent@0__:expired')
        
        logger.info("Started listening for Redis conversation key expiration events")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                expired_key = message['data'].decode('utf-8')
                
                # Only process conversation keys with our prefix
                if expired_key.startswith(REDIS_PREFIX + 'conversation_'):
                    await cleanup_mongodb_on_expiration(expired_key)
                    
    except Exception as e:
        logger.error(f"Error in Redis expiration listener: {str(e)}")
    finally:
        if pubsub:
            await pubsub.close()
        if redis_client:
            await redis_client.close()


async def cleanup_mongodb_on_expiration(expired_key: str):
    """
    Parse expired Redis key and delete corresponding MongoDB records.
    
    Args:
        expired_key (str): The expired Redis key
    """
    try:
        # Remove Redis prefix
        key = expired_key[len(REDIS_PREFIX):] if expired_key.startswith(REDIS_PREFIX) else expired_key
        
        # Parse conversation key: conversation_{org_id}_{bridge_id}_{version_id}_{thread_id}_{sub_thread_id}
        pattern = r'^conversation_([^_]+)_([^_]+)_([^_]+)_([^_]+)_(.+)$'
        match = re.match(pattern, key)
        
        if match:
            org_id, bridge_id, version_id, thread_id, sub_thread_id = match.groups()
            
            # Delete matching MongoDB records
            query = {
                'org_id': org_id,
                'bridge_id': bridge_id,
                'version_id': version_id,
                'thread_id': thread_id,
                'sub_thread_id': sub_thread_id
            }
            
            result = await threadsModel.delete_many(query)
            
            if result.deleted_count > 0:
                logger.info(f"Deleted {result.deleted_count} thread records for expired key: {key}")
            else:
                logger.info(f"No thread records found for expired key: {key}")
                
        else:
            logger.warning(f"Could not parse conversation key: {key}")
            
    except Exception as e:
        logger.error(f"Error cleaning up MongoDB for expired key {expired_key}: {str(e)}")
