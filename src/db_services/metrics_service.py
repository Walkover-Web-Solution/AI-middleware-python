
import json
import uuid
import traceback
from datetime import datetime, timezone
import asyncio
from numpy import version
from models.index import combined_models
from sqlalchemy import and_
from ..controllers.conversationController import savehistory
from .conversationDbService import insertRawData, timescale_metrics
from ..services.cache_service import find_in_cache, store_in_cache
from ..services.utils.check_limit import update_limit_cache_usage
from globals import *
# from src.services.utils.send_error_webhook import send_error_to_webhook
from src.configs.constant import redis_keys

postgres = combined_models['pg']
timescale = combined_models['timescale']

def start_of_today():
    today = datetime.now()
    return datetime(today.year, today.month, today.day, 0, 0, 0, 0)

async def save_conversations_to_redis(conversations, version_id, thread_id, sub_thread_id, history_params):
    """
    Save conversations to Redis with conversation management logic.
    If conversation array has more than 9 items, remove first 2 and add current conversation.
    """
    try:
        # Create Redis key
        redis_key = f"{redis_keys['conversation_']}{version_id}_{thread_id}_{sub_thread_id}"
        # Start with existing conversations from database
        conversation_list = conversations or []
        
        # Create current conversation entries (user + assistant)
        current_time = datetime.now().isoformat() + "+00:00"
        
        # User message
        user_conversation = {
            "content": history_params['user'],
            "role": "user", 
            "createdAt": current_time,
            "id": int(str(uuid.uuid4().int)[:8]),  # Generate 8-digit ID
            "function": None,
            "is_reset": False,
            "tools_call_data": history_params.get('tools_call_data'),
            "error": "",
            "urls": history_params.get('urls', [])
        }
        
        # Assistant message  
        assistant_conversation = {
            "content": history_params.get('message', ''),
            "role": "assistant",
            "createdAt": current_time, 
            "id": int(str(uuid.uuid4().int)[:8]),  # Generate 8-digit ID
            "function": {},
            "is_reset": False,
            "tools_call_data": None,
            "error": None,
            "urls": []
        }
        
        # Add new conversations first
        conversation_list.extend([user_conversation, assistant_conversation])
        
        # Manage conversation array size - if more than 9, remove first 2
        if len(conversation_list) > 9:
            # Remove first 2 conversations
            conversation_list = conversation_list[2:]
        
        # Save to Redis with 30 days TTL (30 * 24 * 60 * 60 = 2592000 seconds)
        ttl_30_days = 2592000
        await store_in_cache(redis_key, conversation_list, ttl_30_days)
        
        logger.info(f"Saved conversations to Redis with key: {redis_key}")
        
    except Exception as error:
        logger.error(f"Error saving conversations to Redis: {str(error)}")
        logger.error(traceback.format_exc())

def end_of_today():
    today = datetime.now()
    return datetime(today.year, today.month, today.day, 23, 59, 59, 999)

async def find(org_id, start_time=None, end_time=None, limit=None, offset=None):
    date_filter = and_(start_time, end_time) if start_time and end_time else and_(start_of_today(), end_of_today())
    query_options = {
        'where': {
            'org_id': org_id,
            'created_at': date_filter
        },
        'limit': limit,
        'offset': offset
    }
    model = timescale.daily_data if start_time and end_time else timescale.five_minute_data
    return await model.find_all(**query_options)

async def find_one(id):
    model = timescale.raw_data
    return await model.find_by_pk(id)

async def find_one_pg(id):
    model = postgres.raw_data
    return await model.find_by_pk(id)

async def create(dataset, history_params, version_id, thread_info={}):
    try:
        conversations = []
        if thread_info is not None:
            thread_id = thread_info.get('thread_id')
            sub_thread_id = thread_info.get('sub_thread_id')
            conversations = thread_info.get('result', [])
        result = await try_catch (
            savehistory,
            history_params['thread_id'], history_params['sub_thread_id'], history_params['user'], history_params['message'],
            history_params['org_id'], history_params['bridge_id'], history_params['model'],
            history_params['channel'], history_params['type'], history_params['actor'],
            history_params.get('tools'),history_params.get('chatbot_message'),history_params.get('tools_call_data'),history_params.get('message_id'), version_id, history_params.get('image_urls'), history_params.get('revised_prompt'), history_params.get('urls'), history_params.get('AiConfig'), history_params.get('annotations'), history_params.get('fallback_model')
        )
        response = history_params.get('response',{})

        # Save conversations to Redis with TTL of 30 days
        if 'error' not in dataset[0] and conversations:
                await save_conversations_to_redis(conversations, version_id, thread_id, sub_thread_id, history_params)
        
        chat_id = result[0]
        dataset[0]['chat_id'] = chat_id
        dataset[0]['message_id'] = history_params.get('message_id')

        insert_ai_data_in_pg = [
            {
                'org_id': data_object['orgId'],
                'authkey_name': data_object.get('apikey_object_id', {}).get(data_object['service'], '') if data_object.get('apikey_object_id') else '',
                'latency': data_object.get('latency', 0),
                'service': data_object['service'],
                'status': data_object.get('success', False),
                'error': data_object.get('error', '') if not data_object.get('success', False) else '',
                'model': data_object['model'],
                'input_tokens': data_object.get('inputTokens', 0),
                'output_tokens': data_object.get('outputTokens', 0),
                'expected_cost': data_object.get('expectedCost', 0),
                'created_at': datetime.now(),
                'chat_id': data_object.get('chat_id'),
                'message_id': data_object.get('message_id'),
                'variables': data_object.get('variables') or {},
                'is_present': 'prompt' in data_object,
                'id' : str(uuid.uuid4()),
                'firstAttemptError' : history_params.get('firstAttemptError'),
                'finish_reason' : response.get('data', {}).get('finish_reason')
            }
            for data_object in dataset
        ]
        await insertRawData(insert_ai_data_in_pg)
        latency = json.loads(dataset[0].get('latency', 0)).get('over_all_time') or 0
        metrics_data = [
            {
                'org_id': data_object['orgId'],
                'bridge_id': history_params['bridge_id'],
                'version_id' : version_id,
                'thread_id': history_params['thread_id'],
                'model': data_object['model'],
                'input_tokens': data_object.get('inputTokens', 0) or 0.0,
                'output_tokens': data_object.get('outputTokens', 0) or 0.0,
                'total_tokens': data_object.get('totalTokens', 0) or 0.0,
                'apikey_id': data_object.get('apikey_object_id', {}).get(data_object['service'], '') if data_object.get('apikey_object_id') else '',
                'created_at': datetime.now(),  # Remove timezone to match database expectations
                'latency': latency,
                'success' : data_object.get('success', False),
                'cost' : data_object.get('expectedCost', 0) or 0.0,
                'time_zone' : 'Asia/Kolkata',
                'service' : data_object['service']
            }
            for data_object in dataset
        ]
        
        # Create the cache key based on bridge_id (assuming it's always available)
        cache_key = f"{redis_keys['metrix_bridges_']}{history_params['bridge_id']}"
        # Safely load the old total token value from the cache
        cache_value = await find_in_cache(cache_key)
        try:
            oldTotalToken = json.loads(cache_value) if cache_value else 0
        except (json.JSONDecodeError, TypeError):
            oldTotalToken = 0

        # Calculate the total token sum, using .get() for 'totalTokens' to handle missing keys
        totaltoken = sum(data_object.get('totalTokens', 0) for data_object in dataset) + oldTotalToken
        # await send_error_to_webhook(history_params['bridge_id'], history_params['org_id'],totaltoken , 'metrix_limit_reached')
        await store_in_cache(cache_key, float(totaltoken))
        await timescale_metrics(metrics_data)
    except Exception as error:
        logger.error(f'Error during bulk insert of Ai middleware, {str(error)}')

# DEPRECATED: This function has been replaced by update_limit_cache_usage_from_metrics
# The old bridge cache logic is no longer used - we now use separate limit cache
# async def update_bridge_usage_in_cache(dataset, history_params, version_id):
#     """DEPRECATED: Replaced by limit cache system"""
#     pass

async def update_limit_cache_usage_from_metrics(dataset, history_params, version_id):
    """Optimized limit cache update from metrics data"""
    try:
        # Calculate total cost
        total_cost = sum(item.get('expectedCost', 0) for item in dataset)
        
        if total_cost <= 0:
            return
        
        # Get bridge data
        bridge_id = history_params.get('bridge_id')
        cache_key = f"{version_id}"
        cached_data = await find_in_cache(cache_key)
        
        if not cached_data:
            logger.warning(f"No bridge cache found: {cache_key}")
            return
        
        bridge_data = json.loads(cached_data)
        bridges_info = bridge_data.get('bridges', {})
        
        if not bridges_info:
            return
        
        # Extract identifiers
        folder_id = bridges_info.get('folder_id')
        service = bridges_info.get('service')
        apikey_object_id = bridges_info.get('apikey_object_id', {}).get(service) if service else None
        
        # Prepare cache updates
        cache_updates = []
        
        # Bridge cache
        if bridge_id:
            cache_updates.append({
                'key': f"bridgelimit_{bridge_id}",
                'limit_field': 'bridge_limit',
                'uses_field': 'bridge_uses',
                'data_source': bridges_info
            })
        
        # Folder cache
        if folder_id:
            cache_updates.append({
                'key': f"folderlimit_{folder_id}",
                'limit_field': 'folder_limit', 
                'uses_field': 'folder_uses',
                'data_source': bridges_info
            })
        
        # API cache
        if service and apikey_object_id:
            api_data = bridge_data.get('apikeys', {}).get(service, {})
            if api_data:
                cache_updates.append({
                    'key': f"apilimit_{apikey_object_id}",
                    'limit_field': 'apikey_limit',
                    'uses_field': 'apikey_uses', 
                    'data_source': api_data
                })
        
        # Execute all updates concurrently
        if cache_updates:
            await asyncio.gather(*[
                _update_single_limit_cache(update, total_cost) 
                for update in cache_updates
            ], return_exceptions=True)
            
            logger.info(f"Updated {len(cache_updates)} limit caches with cost: {total_cost}")
        
    except Exception as e:
        logger.error(f"Error updating limit cache: {str(e)}")

async def _update_single_limit_cache(cache_config, usage_delta):
    """Optimized single cache update with create-or-update logic"""
    try:
        cache_key = cache_config['key']
        data_source = cache_config['data_source']
        
        # Try to get existing cache
        existing_cache = await find_in_cache(cache_key)
        
        if existing_cache:
            # Update existing cache
            cache_data = json.loads(existing_cache)
            cache_data['uses'] = float(cache_data.get('uses', 0)) + float(usage_delta)
        else:
            # Create new cache from database values
            current_uses = float(data_source.get(cache_config['uses_field'], 0) or 0)
            cache_data = {
                'limit': data_source.get(cache_config['limit_field'], 0),
                'uses': current_uses + float(usage_delta)
            }
        # Store updated cache
        await store_in_cache(cache_key, cache_data)
        
    except Exception as e:
        logger.error(f"Error updating cache {cache_config['key']}: {str(e)}")
        raise
# Exporting functions
__all__ = ["find", "create", "find_one", "find_one_pg"]