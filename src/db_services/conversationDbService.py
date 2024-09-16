
from models.index import combined_models as models
import sqlalchemy as sa
from sqlalchemy import func, and_ , insert, delete, or_
from sqlalchemy.exc import SQLAlchemyError
import asyncio
import traceback
from datetime import datetime
from models.postgres.pg_models import Conversation, RawData, system_prompt_versionings

pg = models['pg']

    
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

async def find(org_id, thread_id, bridge_id):
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
                RawData.error
            )
            .outerjoin(RawData, Conversation.id == RawData.chat_id)
            .filter(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.thread_id == thread_id,
                    Conversation.bridge_id == bridge_id,
                    or_(RawData.error == '', RawData.error.is_(None)),
                    Conversation.message_by.in_(["user", "assistant"])
                )
            )
            .order_by(Conversation.id.desc())
            .limit(6)
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

async def reset_chat_history(bridge_id, thread_id):
    session = pg['session']()
    try:
        conversation = (
            session.query(Conversation)
            .filter(
                and_(
                    Conversation.bridge_id == bridge_id,
                    Conversation.thread_id == thread_id
                )
            )
            .order_by(Conversation.id.desc())
            .first()
        )
        
        if conversation:
            # Update the fetched record
            conversation.is_reset = True
            session.commit()
            return {
                'success': True,
                'message': 'Chatbot reset successfully',
                'result': conversation.id
            }
        else:
            return {
                'success': False,
                'message': 'No conversation found to reset',
                'result': None
            }
    except Exception as error:
        session.rollback()
        return {
            'success': False,
            'message': 'Error resetting chatbot',
            'result': error
        }
    finally:
        session.close()

# async def getHistory(bridge_id, timestamp):
#     try:
#         history = await models['pg'].system_prompt_versionings.find_all(
#             where=and_(
#                 models['pg'].system_prompt_versionings.bridge_id == bridge_id,
#                 models['pg'].system_prompt_versionings.updated_at <= timestamp
#             ),
#             order=[('updated_at', 'DESC')],
#             limit=1
#         )
#         if history:
#             return { 'success': True, 'system_prompt': history[0].system_prompt }
#         else:
#             return { 'success': False, 'message': "Prompt not found" }
#     except SQLAlchemyError as e:
#         print("get history system prompt error=>", e)
#         return { 'success': False, 'message': "Prompt not found" }

# async def getAllPromptHistory(bridge_id, page, pageSize):
#     try:
#         history = await models['pg'].system_prompt_versionings.find_all(
#             where=models['pg'].system_prompt_versionings.bridge_id == bridge_id,
#             order=[('updated_at', 'DESC')],
#             raw=True,
#             limit=pageSize,
#             offset=(page - 1) * pageSize
#         )
#         if not history:
#             return { 'success': True, 'message': "No prompts found for the given bridge_id" }
#         return { 'success': True, 'history': history }
#     except SQLAlchemyError as e:
#         print("get history system prompt error=>", e)
#         return { 'success': False, 'message': "Error retrieving prompts" }

# async def findMessage(org_id, thread_id, bridge_id):
#     try:
#         conversations = await models['pg'].conversations.find_all(
#             attributes=[('message', 'content'), ('message_by', 'role'), 'createdAt', 'id', 'function'],
#             include=[{
#                 'model': models['pg'].raw_data,
#                 'as': 'raw_data',
#                 'attributes': ['*'],
#                 'required': False,
#                 'on': {
#                     'id': models['pg'].sequelize.where(
#                         models['pg'].sequelize.col('conversations.id'),
#                         '=',
#                         models['pg'].sequelize.col('raw_data.chat_id')
#                     )
#                 }
#             }],
#             where=and_(
#                 models['pg'].conversations.org_id == org_id,
#                 models['pg'].conversations.thread_id == thread_id,
#                 models['pg'].conversations.bridge_id == bridge_id
#             ),
#             order=[('id', 'DESC')],
#             raw=True
#         )
#         conversations = conversations[::-1]
#         return conversations
#     except SQLAlchemyError as e:
#         raise e

# def deleteLastThread(org_id, thread_id, bridge_id):
#     try:
#         session = pg['session']()
#         query = (
#             sa.select(pg['conversations'])
#             .where(
#                 and_(
#                     pg['conversations'].c.org_id == org_id,
#                     pg['conversations'].c.thread_id == thread_id,
#                     pg['conversations'].c.bridge_id == bridge_id,
#                     pg['conversations'].c.message_by == "tool_calls"
#                 )
#             )
#             .order_by(pg['conversations'].c.id.desc())
#             .limit(1)
#         )
#         result = session.execute(query)
#         record_to_delete = result.fetchone()
#         if record_to_delete:
#             session.delete(record_to_delete)
#             session.commit()
#             return {'success': True}
#         return {'success': False}
    
#     except SQLAlchemyError as e:
#         session.rollback()
#         raise e
#     finally:
#         session.close()


# async def findAllThreads(bridge_id, org_id, page, pageSize):
#     try:
#         threads = await models['pg'].conversations.find_all(
#             attributes=[
#                 'thread_id',
#                 (func.min(models['pg'].conversations.id), 'id'),
#                 'bridge_id',
#                 (func.max(models['pg'].conversations.updatedAt), 'updatedAt')
#             ],
#             where=and_(
#                 models['pg'].conversations.bridge_id == bridge_id,
#                 models['pg'].conversations.org_id == org_id
#             ),
#             group=['thread_id', 'bridge_id'],
#             order=[
#                 (models['pg'].conversations.updatedAt, 'DESC'),
#                 ('thread_id', 'ASC')
#             ],
#             limit=pageSize,
#             offset=(page - 1) * pageSize
#         )
#         return threads
#     except SQLAlchemyError as e:
#         raise e


# # Exporting the functions
# __all__ = [
#     'find',
#     'createBulk',
#     'findAllThreads',
#     'deleteLastThread',
#     'storeSystemPrompt',
#     'getHistory',
#     'findMessage',
#     'getAllPromptHistory'
# ]