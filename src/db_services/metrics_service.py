
import json
import uuid
import traceback
from datetime import datetime, timezone
from models.index import combined_models
from sqlalchemy import and_
from ..controllers.conversationController import savehistory
from .conversationDbService import insertRawData, timescale_metrics
from ..services.cache_service import find_in_cache, store_in_cache, delete_in_cache
from globals import *
from src.services.commonServices.baseService.utils import safe_float
from src.configs.constant import redis_keys, service_name
from fastapi import HTTPException
# from src.services.utils.send_error_webhook import send_error_to_webhook

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
        redis_key = f"conversation_{version_id}_{thread_id}_{sub_thread_id}"
        
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
        metrics_data = [
            {
                'org_id': data_object['orgId'],
                'bridge_id': history_params['bridge_id'],
                'version_id' : version_id,
                'thread_id': history_params['thread_id'],
                'model': data_object['model'],
                'input_tokens': safe_float(data_object.get('inputTokens', 0), 0.0, "inputTokens"),
                'output_tokens': safe_float(data_object.get('outputTokens', 0), 0.0, "outputTokens"),
                'total_tokens': safe_float(data_object.get('totalTokens', 0),0.0, "totalTokens"),
                'apikey_id': data_object.get('apikey_object_id', {}).get(data_object['service'], '') if data_object.get('apikey_object_id') else '',
                'created_at': datetime.now(),  # Remove timezone to match database expectations
                'latency': safe_float(json.loads(data_object.get('latency', {})).get('over_all_time', 0),0.0, "over_all_time"),
                'success' : data_object.get('success', False),
                'cost' : safe_float(data_object.get('expectedCost', 0), 0.0, 'expectedCost'),
                'time_zone' : 'Asia/Kolkata',
                'service' : data_object['service']
            }
            for data_object in dataset
        ]
        await insertRawData(insert_ai_data_in_pg)
        
        # Create the cache key based on bridge_id (assuming it's always available)
        cache_key = f"metrix_bridges{history_params['bridge_id']}"

        # Safely load the old total token value from the cache
        cache_value = await find_in_cache(cache_key)
        try:
            oldTotalToken = json.loads(cache_value) if cache_value else 0
        except (json.JSONDecodeError, TypeError):
            oldTotalToken = 0

        # Calculate the total token sum, using .get() for 'totalTokens' to handle missing keys
        totaltoken = sum(data_object.get('totalTokens', 0) for data_object in dataset) + oldTotalToken
        await check_and_handle_quota(dataset, metrics_data[0])
        # await send_error_to_webhook(history_params['bridge_id'], history_params['org_id'],totaltoken , 'metrix_limit_reached')
        await store_in_cache(cache_key, float(totaltoken))
        await timescale_metrics(metrics_data)
    except Exception as error:
        logger.error(f'Error during bulk insert of Ai middleware, {str(error)}')

async def check_and_handle_quota(dataset, metrics_data):
    try:
        bridge_cache_key = f"{redis_keys['bridge_quota']}_{metrics_data['bridge_id']}"
        bridge_quota = await find_in_cache(bridge_cache_key)
        bridge_quota = json.loads(bridge_quota.decode("utf-8")) if isinstance(bridge_quota, bytes) else bridge_quota
        bridge_quota = bridge_quota if bridge_quota is not None else bridge_data.get('bridge_quota', {})
        if bridge_quota and 'limit' in bridge_quota and 'used' in bridge_quota:
            bridge_quota['used'] = metrics_data.get('total_cost', 0) + bridge_quota.get("used",0)
            if bridge_quota['limit'] <= bridge_quota['used']:
                raise HTTPException(status_code=429, detail="Bridge quota limit reached for the bridge.")
            await store_in_cache(bridge_cache_key, bridge_quota)
        
    except HTTPException as e:
        logger.error(f'Bridge quota limit reached for the bridge.')
        raise e
    
    except Exception as e:
        logger.error(f'Error in handling bridge quota {e}')
        

    try:
        apikey_object_id = metrics_data['apikey_id']
        apikey_cache_key = f"{redis_keys['apikey_quota']}_{apikey_object_id}"
        apikey_quota = await find_in_cache(apikey_cache_key)
        apikey_quota = json.loads(apikey_quota.decode("utf-8")) if isinstance(apikey_quota, bytes) else apikey_quota
        if apikey_quota and 'limit' in apikey_quota and 'used' in apikey_quota:
            apikey_quota['used'] = metrics_data.get('cost', 0) + apikey_quota.get("used",0)
            if apikey_quota['limit'] <= apikey_quota['used']:
                raise HTTPException(status_code=429, detail="API key quota limit reached for the API key used.")
            await store_in_cache(apikey_cache_key, apikey_quota)

    except HTTPException as e:
        logger.error(f'API key quota limit reached for the API key used.')
        raise e
    except Exception as e:
        logger.error(f'Error in handling API key quota {e}')
        

# Exporting functions
__all__ = ["find", "create", "find_one", "find_one_pg"]
