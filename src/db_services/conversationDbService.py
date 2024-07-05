
from models.index import combined_models as models
from sqlalchemy import func, and_ , insert
from sqlalchemy.exc import SQLAlchemyError
import asyncio
import traceback
from datetime import datetime

pg = models['pg']

async def createBulk(data):
    try:
        for i in data :
            i['createdAt'] = datetime.now()
            i['updatedAt'] = datetime.now()
        result = pg['session'].execute(
            insert(pg['conversations']).returning(pg['conversations'].c.id),
            data
        )
        models['pg']['session'].commit()
        rows = result.fetchall()
        results=list(rows[0])
        return results
    except Exception as e:
        await models['pg']['session'].rollback()
        raise e
    
async def insertRawData(data) :
    print('in insert raw data')
    try:
        pg['session'].execute(
            insert(pg['raw_data']), data
        )
        pg['session'].commit()
    except Exception as e:
        models['pg']['session'].rollback()
        raise e

async def find(org_id, thread_id, bridge_id):
    try:
        conversations = await models['pg'].conversations.find_all(
            attributes=[('message', 'content'), ('message_by', 'role'), 'createdAt', 'id', 'function'],
            where=and_(
                models['pg'].conversations.org_id == org_id,
                models['pg'].conversations.thread_id == thread_id,
                models['pg'].conversations.bridge_id == bridge_id
            ),
            order=[('id', 'DESC')],
            limit=6,
            raw=True
        )
        conversations = conversations[::-1]
        return conversations
    except SQLAlchemyError as e:
        raise e

async def getHistory(bridge_id, timestamp):
    try:
        history = await models['pg'].system_prompt_versionings.find_all(
            where=and_(
                models['pg'].system_prompt_versionings.bridge_id == bridge_id,
                models['pg'].system_prompt_versionings.updated_at <= timestamp
            ),
            order=[('updated_at', 'DESC')],
            limit=1
        )
        if history:
            return { 'success': True, 'system_prompt': history[0].system_prompt }
        else:
            return { 'success': False, 'message': "Prompt not found" }
    except SQLAlchemyError as e:
        print("get history system prompt error=>", e)
        return { 'success': False, 'message': "Prompt not found" }

async def getAllPromptHistory(bridge_id, page, pageSize):
    try:
        history = await models['pg'].system_prompt_versionings.find_all(
            where=models['pg'].system_prompt_versionings.bridge_id == bridge_id,
            order=[('updated_at', 'DESC')],
            raw=True,
            limit=pageSize,
            offset=(page - 1) * pageSize
        )
        if not history:
            return { 'success': True, 'message': "No prompts found for the given bridge_id" }
        return { 'success': True, 'history': history }
    except SQLAlchemyError as e:
        print("get history system prompt error=>", e)
        return { 'success': False, 'message': "Error retrieving prompts" }

async def findMessage(org_id, thread_id, bridge_id):
    try:
        conversations = await models['pg'].conversations.find_all(
            attributes=[('message', 'content'), ('message_by', 'role'), 'createdAt', 'id', 'function'],
            include=[{
                'model': models['pg'].raw_data,
                'as': 'raw_data',
                'attributes': ['*'],
                'required': False,
                'on': {
                    'id': models['pg'].sequelize.where(
                        models['pg'].sequelize.col('conversations.id'),
                        '=',
                        models['pg'].sequelize.col('raw_data.chat_id')
                    )
                }
            }],
            where=and_(
                models['pg'].conversations.org_id == org_id,
                models['pg'].conversations.thread_id == thread_id,
                models['pg'].conversations.bridge_id == bridge_id
            ),
            order=[('id', 'DESC')],
            raw=True
        )
        conversations = conversations[::-1]
        return conversations
    except SQLAlchemyError as e:
        raise e

async def deleteLastThread(org_id, thread_id, bridge_id):
    try:
        record_to_delete = await models['pg'].conversations.find_one(
            where=and_(
                models['pg'].conversations.org_id == org_id,
                models['pg'].conversations.thread_id == thread_id,
                models['pg'].conversations.bridge_id == bridge_id,
                models['pg'].conversations.message_by == "tool_calls"
            ),
            order=[('id', 'DESC')]
        )
        if record_to_delete:
            await record_to_delete.delete()
            await models['pg'].session.commit()
            return { 'success': True }
        return { 'success': False }
    except SQLAlchemyError as e:
        await models['pg'].session.rollback()
        raise e

async def findAllThreads(bridge_id, org_id, page, pageSize):
    try:
        threads = await models['pg'].conversations.find_all(
            attributes=[
                'thread_id',
                (func.min(models['pg'].conversations.id), 'id'),
                'bridge_id',
                (func.max(models['pg'].conversations.updatedAt), 'updatedAt')
            ],
            where=and_(
                models['pg'].conversations.bridge_id == bridge_id,
                models['pg'].conversations.org_id == org_id
            ),
            group=['thread_id', 'bridge_id'],
            order=[
                (models['pg'].conversations.updatedAt, 'DESC'),
                ('thread_id', 'ASC')
            ],
            limit=pageSize,
            offset=(page - 1) * pageSize
        )
        return threads
    except SQLAlchemyError as e:
        raise e

async def storeSystemPrompt(promptText, orgId, bridgeId):
    try:
        await models['pg'].system_prompt_versionings.create(
            system_prompt=promptText,
            org_id=orgId,
            bridge_id=bridgeId,
            created_at=func.now(),
            updated_at=func.now()
        )
        await models['pg'].session.commit()
    except SQLAlchemyError as e:
        await models['pg'].session.rollback()
        print('Error storing system prompt:', e)

# Exporting the functions
__all__ = [
    'find',
    'createBulk',
    'findAllThreads',
    'deleteLastThread',
    'storeSystemPrompt',
    'getHistory',
    'findMessage',
    'getAllPromptHistory'
]