import json
from models.index import combined_models as models
import sqlalchemy as sa
from sqlalchemy import func, and_ , insert, delete, or_ , update, select
from sqlalchemy.exc import SQLAlchemyError
from ..services.cache_service import find_in_cache, store_in_cache
from datetime import datetime
from models.postgres.pg_models import Conversation, RawData, system_prompt_versionings, user_bridge_config_history, ConversationLog
from models.Timescale.timescale_models import Metrics_model
from sqlalchemy.sql import text
from globals import *
from datetime import timedelta

pg = models['pg']
timescale = models['timescale']

    
def createBulk(conversations_data):
    session = pg['session']()
    try:
        conversations = [Conversation(**data) for data in conversations_data]
        session.add_all(conversations)
        session.commit()
        return [conversation.id for conversation in conversations]
    except Exception as err :
        logger.error(f"Error in creating bulk conversations: {str(err)}")
        session.rollback()
    finally : 
        session.close()


async def createConversationLog(conversation_log_data):
    """
    Create a single consolidated conversation log entry
    
    Args:
        conversation_log_data: Dictionary containing all conversation data
        
    Returns:
        Integer ID of created record or None if failed
    """
    session = pg['session']()
    try:
        conversation_log = ConversationLog(**conversation_log_data)
        session.add(conversation_log)
        session.commit()
        return conversation_log.id
    except Exception as err:
        logger.error(f"Error in creating conversation log: {str(err)}")
        session.rollback()
        return None
    finally:
        session.close()


async def insertRawData(raw_data) : 
    session = pg['session']()
    try:
        raws = [RawData(**data) for data in raw_data]
        session.add_all(raws)
        session.commit()
    except Exception as e: 
        session.rollback()
        raise e

async def find(org_id, thread_id, sub_thread_id, bridge_id):
    try:
        session = pg['session']()
        conversations = (
            session.query(
                Conversation.message.label('content'),
                Conversation.message_by.label('role'),
                Conversation.createdAt,
                Conversation.id,
                Conversation.function,
                Conversation.is_reset,
                Conversation.tools_call_data,
                RawData.error,
                func.coalesce(Conversation.urls, []).label('urls')  # Updated to handle 'urls' as an array
            )
            .outerjoin(RawData, Conversation.id == RawData.chat_id)
            .filter(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.thread_id == thread_id,
                    Conversation.bridge_id == bridge_id,
                    Conversation.sub_thread_id == sub_thread_id,
                    or_(RawData.error == '', RawData.error.is_(None)),
                    Conversation.message_by.in_(["user", "tools_call", "assistant"])
                )
            )
            .order_by(Conversation.id.desc())
            .limit(9)
            .all()
        )
        conversations.reverse()
        return [conversation._asdict() for conversation in conversations]
    except Exception as e:
        logger.error(f"Error in finding conversations: {str(e)}")
        return []
    finally:
        session.close()


async def find_conversation_logs(org_id, thread_id, sub_thread_id):
    """
    Find conversation logs from the new consolidated conversation_logs table
    
    Args:
        org_id: Organization ID
        thread_id: Thread ID
        sub_thread_id: Sub-thread ID
        
    Returns:
        List of conversation logs formatted for response
    """
    try:
        session = pg['session']()
        logs = (
            session.query(ConversationLog)
            .filter(
                and_(
                    ConversationLog.org_id == org_id,
                    ConversationLog.thread_id == thread_id,
                    ConversationLog.sub_thread_id == sub_thread_id,
                    ConversationLog.status == True  # Only successful conversations
                )
            )
            .order_by(ConversationLog.created_at.desc())
            .limit(9)
            .all()
        )
        
        # Convert logs to conversation format expected by the application
        conversations = []
        for log in reversed(logs):
            # Add user message
            if log.user:
                conversations.append({
                    'content': log.user,
                    'role': 'user',
                    'createdAt': log.created_at,
                    'id': log.id,
                    'function': None,
                    'is_reset': False,
                    'tools_call_data': log.tools_call_data,
                    'error': '',
                    'urls': log.urls or []
                })
            
            # Add tools_call if present
            if log.tools_call_data:
                conversations.append({
                    'content': '',
                    'role': 'tools_call',
                    'createdAt': log.created_at,
                    'id': log.id,
                    'function': {},
                    'is_reset': False,
                    'tools_call_data': log.tools_call_data,
                    'error': '',
                    'urls': []
                })
            
            # Add assistant message
            if log.chatbot_message or log.llm_message:
                conversations.append({
                    'content': log.chatbot_message or log.llm_message,
                    'role': 'assistant',
                    'createdAt': log.created_at,
                    'id': log.id,
                    'function': {},
                    'is_reset': False,
                    'tools_call_data': None,
                    'error': '',
                    'urls': []
                })
        
        return conversations
    except Exception as e:
        logger.error(f"Error in finding conversation logs: {str(e)}")
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
                func.avg(
                    func.cast(
                        # Use the proper JSONB extraction for PostgreSQL
                        func.jsonb_extract_path_text(RawData.latency, 'over_all_time'),
                        sa.Float
                    )
                ).label('avg_response_time')
            )
            .select_from(Conversation)
            .join(RawData, Conversation.id == RawData.chat_id)
            .filter(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.bridge_id == bridge_id,
                    Conversation.message_by == 'user',
                    or_(RawData.error == '', RawData.error.is_(None)),
                    RawData.created_at >= yesterday_start,
                    RawData.created_at <= yesterday_end
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

async def reset_and_mode_chat_history(org_id, bridge_id, thread_id, key, value):
    session = pg['session']()
    try:
        subquery = (
            select(Conversation.id)
            .where(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.bridge_id == bridge_id,
                    Conversation.thread_id == thread_id
                )
            )
            .order_by(Conversation.id.desc())
            .limit(1)
        )
        stmt = (
            update(Conversation)
            .where(Conversation.id == subquery.scalar_subquery())
            .values({key: value})
            .returning(Conversation.id)
        )
        result = session.execute(stmt)
        updated_conversation = result.fetchone()
        if updated_conversation:
            session.commit()
            return {
                'success': True,
                'message': 'Chatbot reset successfully',
                'result': updated_conversation.id
            }
        else:
            return {
                'success': True,
                'message': 'No conversation found to reset',
                'result': None
            }
    except Exception as error:
        session.rollback()
        return {
            'success': False,
            'message': 'Error resetting chatbot',
            'result': str(error)
        }
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