import json
from models.index import combined_models as models
from sqlalchemy import func, and_ , or_ , update, select
from ..services.cache_service import find_in_cache, store_in_cache
from datetime import datetime
from models.postgres.pg_models import Conversation, system_prompt_versionings, user_bridge_config_history
from models.Timescale.timescale_models import Metrics_model
from sqlalchemy.sql import text
from globals import *
from datetime import timedelta

pg = models['pg']
timescale = models['timescale']

async def find(org_id, thread_id, sub_thread_id, bridge_id):
    try:
        session = pg['session']()
        
        conversations = (
            session.query(Conversation)
            .filter(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.thread_id == thread_id,
                    Conversation.bridge_id == bridge_id,
                    Conversation.sub_thread_id == sub_thread_id,
                    or_(Conversation.error == '', Conversation.error.is_(None))
                )
            )
            .order_by(Conversation.id.desc())
            .limit(9)
            .all()
        )
        
        # Convert to format expected by existing code
        result = []
        for conv in reversed(conversations):
            # Create user message entry
            if conv.get('user_message'):
                result.append({
                    'content': conv.get('user_message'),
                    'role': 'user',
                    'createdAt': conv.get('createdAt'),
                    'id': conv.get('id'),
                    'function': {},
                    'is_reset': False,
                    'tools_call_data': conv.get('tools_call_data', []),
                    'error': conv.get('error', ''),
                    'urls': conv.get('urls', [])
                })
            
            # Create tools call entry if exists
            if conv.get('tools_call_data') and len(conv.get('tools_call_data', [])) > 0:
                result.append({
                    'content': '',
                    'role': 'tools_call',
                    'createdAt': conv.get('createdAt'),
                    'id': conv.get('id'),
                    'function': conv.get('tools_call_data', [{}])[0],
                    'is_reset': False,
                    'tools_call_data': conv.get('tools_call_data'),
                    'error': conv.get('error', ''),
                    'urls': []
                })
            
            # Create assistant message entry
            if conv.get('response') or conv.get('chatbot_response'):
                result.append({
                    'content': conv.get('response') or conv.get('chatbot_response'),
                    'role': 'assistant',
                    'createdAt': conv.get('createdAt'),
                    'id': conv.get('id'),
                    'function': {},
                    'is_reset': False,
                    'tools_call_data': None,
                    'error': conv.get('error', ''),
                    'urls': []
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in finding conversations: {str(e)}")
        return []
    finally:
        session.close()
async def calculate_average_response_time(org_id, bridge_id):
    try:
        session = pg['session']()
        # Get current date and yesterday's date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())
        
        query = (
            session.query(
                func.avg(Conversation.latency).label('avg_response_time')
            )
            .filter(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.bridge_id == bridge_id,
                    Conversation.user_message.isnot(None),
                    or_(Conversation.error == '', Conversation.error.is_(None)),
                    Conversation.created_at >= yesterday_start,
                    Conversation.created_at <= yesterday_end
                )
            )
            .scalar()
        )
        
        return query or 0 
    except Exception as e:
        logger.error(f"Error in calculating average response time: {str(e)}")
        return 0
    finally:
        session.close()

async def storeSystemPrompt(prompt, org_id, bridge_id):
    session = pg['session']()
    try:
        new_prompt = system_prompt_versionings(
            system_prompt=prompt,
            org_id=org_id,
            bridge_id=bridge_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(new_prompt)
        session.commit()
        return {
            'id': new_prompt.id
            }
    except Exception as error:
        session.rollback()
        logger.error(f"Error in storing system prompt: {str(error)}")
        raise error
    finally:
        session.close()

async def add_bulk_user_entries(entries):
    session = pg['session']()
    try:
        user_history = [user_bridge_config_history(**data) for data in entries]
        session.add_all(user_history)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error in creating bulk user entries: {str(e)}")
    finally:
        session.close()


async def create_conversation_entry(conversation_data):
    """
    Save conversation entry data to database
    """
    session = pg['session']()
    print(conversation_data)
    try:
        from models.postgres.pg_models import Conversation
        
        conversation_entry = Conversation(**conversation_data)
        session.add(conversation_entry)
        session.commit()
        
        conversation_id = conversation_entry.id
        logger.info(f"Created conversation entry with ID: {conversation_id}")
        
        return conversation_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Database error in create conversation entry: {str(e)}")
        raise e
    finally:
        session.close()

async def timescale_metrics(metrics_data):
    async with timescale['session']() as session:
        try:
            raws = [Metrics_model(**data) for data in metrics_data]
            session.add_all(raws)
            await session.commit()
        except Exception as e:
            print("fail in metrics service", e)
            await session.rollback()
            raise e



async def get_timescale_data(org_id):
    cache_key = f"metrix_{org_id}"
    # Attempt to retrieve data from Redis cache

    cached_data = await find_in_cache(cache_key)
    if cached_data:
        # Deserialize the cached JSON data
        cached_result = json.loads(cached_data)
        return cached_result 
    else:
        try:
            session = timescale['session']()
            query = text(f"""
                SELECT bridge_id,
                        SUM(total_token_count) as total_tokens 
                FROM fifteen_minute_data 
                WHERE org_id = :org_id 
                GROUP BY bridge_id
            """)
            result = await session.execute(query, {'org_id': org_id})
            data = result.fetchall()
            await store_in_cache(cache_key, data, 86400)
            return data
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()