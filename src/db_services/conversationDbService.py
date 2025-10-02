import json
from models.index import combined_models as models
import sqlalchemy as sa
from sqlalchemy import func, and_ , insert, delete, or_ , update, select
from sqlalchemy.exc import SQLAlchemyError
from ..services.cache_service import find_in_cache, store_in_cache
from datetime import datetime
from models.postgres.pg_models import Conversation, RawData, system_prompt_versionings, user_bridge_config_history
from models.Timescale.timescale_models import Metrics_model
from sqlalchemy.sql import text
from globals import *
from datetime import timedelta

pg = models['pg']
timescale = models['timescale']

    
def createBulk(conversations_data):
    """Insert multiple conversation records in a single transaction."""
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


async def insertRawData(raw_data) : 
    """Store raw tracing data associated with chatbot messages."""
    session = pg['session']()
    try:
        raws = [RawData(**data) for data in raw_data]
        session.add_all(raws)
        session.commit()
    except Exception as e: 
        session.rollback()
        raise e

async def find(org_id, thread_id, sub_thread_id, bridge_id):
    """Fetch the latest conversation history for a thread/sub-thread pair."""
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
async def calculate_average_response_time(org_id, bridge_id):
    """Compute yesterday's average response latency for a bridge."""
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
    """Persist a versioned copy of a system prompt."""
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
    """Update the latest conversation row with reset metadata."""
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
    """Log bulk user activity entries for bridge configuration changes."""
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
    """Insert aggregated metrics into the Timescale store."""
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
    """Retrieve cached or fresh usage metrics for an organisation."""
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
