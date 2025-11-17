
import json
import uuid
import traceback
from datetime import datetime, timezone

from models.index import combined_models
from sqlalchemy import and_
from ..controllers.conversationController import savehistory, savehistory_consolidated
from .conversationDbService import insertRawData, timescale_metrics
from ..services.cache_service import find_in_cache, store_in_cache
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
        
        response = history_params.get('response',{})
        
        # Prepare consolidated conversation log data
        data_object = dataset[0]
        
        # Parse latency JSON to extract over_all_time
        latency_data = {}
        try:
            if isinstance(data_object.get('latency'), str):
                latency_data = json.loads(data_object.get('latency', '{}'))
            else:
                latency_data = data_object.get('latency', {})
        except:
            latency_data = {}
        
        conversation_log_data = {
            'llm_message': history_params.get('message', ''),
            'user': history_params.get('user', ''),
            'chatbot_message': history_params.get('chatbot_message', ''),
            'updated_chatbot_message': None,
            'error': str(data_object.get('error', '')) if not data_object.get('success', False) else None,
            'user_feedback': 0,
            'tools_call_data': history_params.get('tools_call_data', []),
            'message_id': str(history_params.get('message_id')),
            'sub_thread_id': history_params.get('sub_thread_id'),
            'thread_id': history_params.get('thread_id'),
            'version_id': version_id,
            'image_urls': history_params.get('image_urls', []),
            'urls': history_params.get('urls', []),
            'AiConfig': history_params.get('AiConfig'),
            'fallback_model': history_params.get('fallback_model'),
            'org_id': data_object.get('orgId') or history_params.get('org_id'),
            'service': data_object.get('service') or history_params.get('service'),
            'model': data_object.get('model') or history_params.get('model'),
            'status': data_object.get('success', False),
            'tokens': {
                'input_tokens': data_object.get('inputTokens', 0),
                'output_tokens': data_object.get('outputTokens', 0),
                'expected_cost': data_object.get('expectedCost', 0)
            },
            'variables': data_object.get('variables') or {},
            'latency': latency_data,
            'firstAttemptError': history_params.get('firstAttemptError'),
            'finish_reason': response.get('data', {}).get('finish_reason'),
            'parent_id': history_params.get('parent_id') or '',
            'bridge_id': history_params.get('bridge_id')
        }
        
        # Save consolidated conversation log
        result_id = await savehistory_consolidated(conversation_log_data)
        
        # Save conversations to Redis with TTL of 30 days
        if 'error' not in dataset[0] and conversations:
            await save_conversations_to_redis(conversations, version_id, thread_id, sub_thread_id, history_params)
        
        # Extract latency for metrics (use already parsed latency_data)
        latency = latency_data.get('over_all_time', 0) if latency_data else 0
        
        # Only create metrics data if dataset has valid data
        metrics_data = []
        for data_object in dataset:
            # Skip empty data objects
            if not data_object or not data_object.get('orgId'):
                continue
                
            service = data_object.get('service', history_params.get('service', ''))
            metrics_data.append({
                'org_id': data_object.get('orgId', history_params.get('org_id')),
                'bridge_id': history_params.get('bridge_id', ''),
                'version_id': version_id,
                'thread_id': history_params.get('thread_id', ''),
                'model': data_object.get('model', history_params.get('model', '')),
                'input_tokens': data_object.get('inputTokens', 0) or 0.0,
                'output_tokens': data_object.get('outputTokens', 0) or 0.0,
                'total_tokens': data_object.get('total_tokens', 0) or 0.0,
                'apikey_id': data_object.get('apikey_object_id', {}).get(service, '') if data_object.get('apikey_object_id') else '',
                'created_at': datetime.now(),
                'latency': latency,
                'success': data_object.get('success', False),
                'cost': data_object.get('expectedCost', 0) or 0.0,
                'time_zone': 'Asia/Kolkata',
                'service': service
            })
        
        # Create the cache key based on bridge_id (assuming it's always available)
        cache_key = f"{redis_keys['metrix_bridges_']}{history_params['bridge_id']}"
        # Safely load the old total token value from the cache
        cache_value = await find_in_cache(cache_key)
        try:
            oldTotalToken = json.loads(cache_value) if cache_value else 0
        except (json.JSONDecodeError, TypeError):
            oldTotalToken = 0

        # Calculate the total token sum, using .get() for 'totalTokens' to handle missing keys
        totaltoken = sum(data_object.get('total_tokens', 0) for data_object in dataset) + oldTotalToken
        # await send_error_to_webhook(history_params['bridge_id'], history_params['org_id'],totaltoken , 'metrix_limit_reached')
        await store_in_cache(cache_key, float(totaltoken))
        
        # Only save metrics if there's valid data
        if metrics_data:
            await timescale_metrics(metrics_data)
    except Exception as error:
        logger.error(f'Error during bulk insert of Ai middleware, {str(error)}')

# Exporting functions
__all__ = ["find", "create", "find_one", "find_one_pg"]