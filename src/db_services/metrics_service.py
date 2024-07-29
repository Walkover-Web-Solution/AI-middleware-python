from datetime import datetime, timedelta
from models.index import combined_models
from sqlalchemy import and_
from ..controllers.conversationController import savehistory
import traceback
from .conversationDbService import insertRawData
import uuid

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

async def create(dataset, history_params):
    try:
        result = await savehistory(
            history_params['thread_id'], history_params['user'], history_params['message'],
            history_params['org_id'], history_params['bridge_id'], history_params['model'],
            history_params['channel'], history_params['type'], history_params['actor'],
            history_params.get('tools')
        )
        
        chat_id = result['result'][0]
        dataset[0]['chat_id'] = chat_id

        insert_ai_data_in_pg = [
            {
                'org_id': data_object['orgId'],
                'authkey_name': data_object.get('authkeyName', 'not_found'),
                'latency': data_object.get('latency', 0),
                'service': data_object['service'],
                'status': data_object.get('success', False),
                'error': data_object.get('error', 'No error') if not data_object.get('success', False) else 'No error',
                'model': data_object['model'],
                'input_tokens': data_object.get('inputTokens', 0),
                'output_tokens': data_object.get('outputTokens', 0),
                'expected_cost': data_object.get('expectedCost', 0),
                'created_at': datetime.now(),
                'chat_id': data_object.get('chat_id'),
                'variables': data_object.get('variables', {}),
                'is_present': 'prompt' in data_object,
                'id' : str(uuid.uuid4())
            }
            for data_object in dataset
        ]

        await insertRawData(insert_ai_data_in_pg)
        # await timescale.raw_data.bulk_create(insert_ai_data)
    except Exception as error:
        traceback.print_exc()
        print('Error during bulk insert of Ai middleware', error)

# Exporting functions
__all__ = ["find", "create", "find_one", "find_one_pg"]
