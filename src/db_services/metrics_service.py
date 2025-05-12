
import json
import uuid
import traceback
from datetime import datetime, timezone
from models.index import combined_models
from sqlalchemy import and_
from ..controllers.conversationController import savehistory
from .conversationDbService import insertRawData, timescale_metrics
from ..services.cache_service import find_in_cache, store_in_cache
from globals import *
# from src.services.utils.send_error_webhook import send_error_to_webhook

postgres = combined_models['pg']
timescale = combined_models['timescale']

def start_of_today():
    today = datetime.now()
    return datetime(today.year, today.month, today.day, 0, 0, 0, 0)

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

async def create(dataset, history_params, version_id):
    try:
        result = await savehistory(
            history_params['thread_id'], history_params['sub_thread_id'], history_params['user'], history_params['message'],
            history_params['org_id'], history_params['bridge_id'], history_params['model'],
            history_params['channel'], history_params['type'], history_params['actor'],
            history_params.get('tools'),history_params.get('chatbot_message'),history_params.get('tools_call_data'),history_params.get('message_id'), version_id, history_params.get('image_url'), history_params.get('revised_prompt'), history_params.get('urls'), history_params.get('AiConfig'), history_params.get('annotations')
        )
        
        chat_id = result['result'][0]
        dataset[0]['chat_id'] = chat_id
        dataset[0]['message_id'] = history_params.get('message_id')

        insert_ai_data_in_pg = [
            {
                'org_id': data_object['orgId'],
                'authkey_name': data_object.get('apikey_object_id', {}).get(data_object['service'], ''),
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
                'firstAttemptError' : history_params.get('firstAttemptError')
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
                'input_tokens': data_object.get('inputTokens', 0),
                'output_tokens': data_object.get('outputTokens', 0),
                'total_tokens': data_object.get('totalTokens', 0),
                'apikey_id': data_object.get('apikey_object_id', {}).get(data_object['service'], ''),
                'created_at': datetime.now(timezone.utc),
                'latency': json.loads(data_object.get('latency', {})).get('over_all_time', 0),
                'success' : data_object.get('success', False),
                'cost' : data_object.get('expectedCost', 0),
                'time_zone' : 'Asia/Kolkata',
                'service' : data_object['service']
            }
            for data_object in dataset
        ]
        await insertRawData(insert_ai_data_in_pg)
        await timescale_metrics(metrics_data)
        cache_key = f"metrix_bridges{history_params['bridge_id']}"
        oldTotalToken = json.loads(await find_in_cache(cache_key) or '0')
        totaltoken = sum(data_object.get('totalTokens', 0) for data_object in dataset) + oldTotalToken
        # await send_error_to_webhook(history_params['bridge_id'], history_params['org_id'],totaltoken , 'metrix_limit_reached')
        await store_in_cache(cache_key, float(totaltoken))
    except Exception as error:
        logger.error(f'Error during bulk insert of Ai middleware, {str(error)}')

# Exporting functions
__all__ = ["find", "create", "find_one", "find_one_pg"]
