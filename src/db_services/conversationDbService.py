from models.index import combined_models as models
import sqlalchemy as sa
from sqlalchemy import func, and_ , insert, delete, or_ , update, select
from sqlalchemy.exc import SQLAlchemyError
import asyncio
import traceback
from datetime import datetime
from models.postgres.pg_models import Conversation, RawData, system_prompt_versionings, user_bridge_config_history
from models.Timescale.timescale_models import Metrics_model

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
        print("Error Inserting in conversations: ", err)
        session.rollback()
    finally : 
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
        print(f"An error occurred: {str(e)}")
        return []
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
        print('Error storing system prompt:', error)
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
        print(f"Error: {e}")
    finally:
        session.close()


async def timescale_metrics(metrics_data) : 
    session = timescale['session']()
    try:
        raws = [Metrics_model(**data) for data in metrics_data]
        session.add_all(raws)
        session.commit()
    except Exception as e: 
        session.rollback()
        raise e