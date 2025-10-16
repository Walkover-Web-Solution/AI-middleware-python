import uuid
import traceback
from datetime import datetime
from .conversationDbService import timescale_metrics, create_conversation_entry
from ..services.cache_service import find_in_cache, store_in_cache
from globals import *
import json

def prepare_conversation_data(primary_data, history_params, version_id, thread_info):
    """
    Prepare conversation entry data combining history params and dataset
    """
    # Determine status based on success
    status = 1 if primary_data.get('success', False) else 0
    
    # Create single conversation entry data
    conversation_data = {
        'org_id': primary_data['orgId'],
        'thread_id': thread_info.get('thread_id'),
        'bridge_id': history_params.get('bridge_id'),
        'user_message': history_params.get('user', ''),
        'response': history_params.get('message', ''),
        'chatbot_response': history_params.get('chatbot_message', ''),
        'tools_call_data': history_params.get('tools_call_data', []),
        'user_feedback': None,
        'version_id': version_id,
        'sub_thread_id': thread_info.get('sub_thread_id'),
        'revised_response': history_params.get('revised_prompt'),
        'image_urls': history_params.get('image_url', []) if history_params.get('image_url') else [],
        'urls': history_params.get('urls', []),
        'fallback_model': history_params.get('fallback_model'),
        'error': primary_data.get('error', '') if not primary_data.get('success', False) else None,
        'status': status,
        'authkey_name': primary_data.get('apikey_object_id', {}).get(primary_data['service'], '') if primary_data.get('apikey_object_id') else '',
        'latency': primary_data.get('latency', 0),
        'service': primary_data['service'],
        'tokens': {"input_tokens": primary_data.get('inputTokens', 0), "output_tokens": primary_data.get('outputTokens', 0), "expected_cost": primary_data.get('expectedCost', 0)},
        'message_id': history_params.get('message_id'),
        'variables': primary_data.get('variables', {}),
        'finish_reason': primary_data.get('finish_reason'),
        'model_name': primary_data['model'],
        'type': history_params.get('type', 'chat'),
        'AiConfig': history_params.get('AiConfig'),
        'annotations': history_params.get('annotations', []),
        'createdAt': datetime.now(),
        'updatedAt': datetime.now(),
    }
    
    return conversation_data

def prepare_timescale_data(dataset, history_params):
    """
    Prepare timescale metrics data
    """
    metrics_data = [
        {
            'org_id': dataset['orgId'],
            'bridge_id': history_params.get('bridge_id'),
            'version_id': history_params.get('version_id'),
            'thread_id': history_params.get('thread_id'),
            'model': history_params.get('model'),
            'input_tokens': dataset.get('inputTokens', 0) or 0.0,
            'output_tokens': dataset.get('outputTokens', 0) or 0.0,
            'total_tokens': dataset.get('totalTokens', 0) or 0.0,
            'apikey_id': dataset.get('apikey_object_id', {}).get(dataset['service'], '') if dataset.get('apikey_object_id') else '',
            'created_at': datetime.now(),  # Remove timezone to match database expectations
            'latency': int(json.loads(dataset.get('latency', {})).get('over_all_time', 0)),
            'success': dataset.get('success', False),
            'cost': dataset.get('expectedCost', 0) or 0.0,
            'time_zone': 'Asia/Kolkata',
            'service': dataset['service']
        }
    ]
    
    return metrics_data

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

async def create(dataset, history_params, version_id, thread_info={}):
    try:
        conversations = []
        if thread_info is not None:
            thread_id = thread_info.get('thread_id')
            sub_thread_id = thread_info.get('sub_thread_id')
            
            # Get existing conversations from Redis
            redis_key = f"conversation_{version_id}_{thread_id}_{sub_thread_id}"
            conversations = await find_in_cache(redis_key) or []
        
        # Create single conversation entry combining history params and dataset
        if dataset and len(dataset) > 0:
            # Get the primary data object (assuming first one contains the main conversation data)
            primary_data = dataset[0]
            
            # Prepare conversation data
            conversation_data = prepare_conversation_data(primary_data, history_params, version_id, thread_info)
            
            # Save conversation entry to database
            conversation_id = await create_conversation_entry(conversation_data)
        
        # Save conversations to Redis
        if thread_info is not None:
            await save_conversations_to_redis(conversations, version_id, thread_id, sub_thread_id, history_params)
        
        # Prepare and insert timescale metrics data
        insert_ai_data_in_pg = prepare_timescale_data(dataset[0], history_params)
        
        await timescale_metrics(insert_ai_data_in_pg)
        
        return
        
    except Exception as error:
        logger.error(f"metrics_service create error: {str(error)}")
        logger.error(traceback.format_exc())
        raise error

# Exporting functions
__all__ = ["create"]
