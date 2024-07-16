from datetime import datetime, timedelta
from models.index import combined_models
from sqlalchemy import func, and_ , insert, update, select
from ..controllers.conversationController import savehistory
import traceback
from .conversationDbService import insertRawData
import uuid
import sqlalchemy as sa

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


async def updateOrCreateLastOptionData(thread_id, data):
    try:
        session = postgres['session']()
        try:
            query = (
                sa.select(
                    postgres['last_data_to_show'].c.thread_id,
                )
                .where(
                    postgres['last_data_to_show'].c.thread_id == thread_id
                )
            )
            result = session.execute(query).fetchone()
            
            if result:
                session.execute(
                    update(postgres['last_data_to_show'])
                    .where(postgres['last_data_to_show'].c.thread_id == thread_id)
                    .values(data=data)
                )
            else:
                session.execute(
                    insert(postgres['last_data_to_show']).values(
                        thread_id=thread_id,
                        data=data
                    )
                )

            session.commit()
        except Exception as e:
            session.rollback()
            traceback.print_exc()
            print(f"Error updating or creating last option data: {e}")
        finally:
            session.close()

    except Exception as e:
        # Print the stack trace and error message if an exception occurs
        traceback.print_exc()
        print(f"Error updating or creating last option data: {e}")


async def findLastOptionData(thread_id):
    model = postgres.last_data_to_show
    return await model.find_one({'thread_id': thread_id})

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
        insert_ai_data = [
            {
                'org_id': data_object['orgId'],
                'authkey_name': data_object.get('authkeyName', 'not_found'),
                'latency': data_object.get('latency', 0),
                'service': data_object['service'],
                'status': data_object.get('success', False),
                'model': data_object['model'],
                'input_tokens': data_object.get('inputTokens', 0),
                'output_tokens': data_object.get('outputTokens', 0),
                'expected_cost': data_object.get('expectedCost', 0),
                'created_at': datetime.now()
            }
            for data_object in dataset
        ]

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
__all__ = ["find", "create", "find_one", "find_one_pg", "updateOrCreateLastOptionData"]
