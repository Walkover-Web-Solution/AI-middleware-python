from src.db_services.conversationDbService import add_bulk_user_entries
from models.mongo_connection import db
from bson import ObjectId
import traceback
import json
import asyncio
from src.services.cache_service import delete_in_cache
from .ConfigurationServices import get_bridges_with_tools, get_bridges_with_tools_and_apikeys, get_bridges_without_tools
from src.services.commonServices.common import chat
from ..services.utils.helper import Helper
from ..services.utils.nlp import compute_cosine_similarity
from ..services.utils.time import Timer
from src.db_services.testcase_services import delete_current_testcase_history
from src.configs.constant import bridge_ids
from ..services.utils.ai_call_util import call_ai_middleware
from globals import *
from src.configs.constant import redis_keys

configurationModel = db["configurations"]
version_model = db['configuration_versions']


async def get_version(org_id, version_id):
    try:
        bridge = await version_model.find_one({'_id' : ObjectId(version_id), 'org_id' : org_id})
        return bridge
    except Exception as e:
        logger.error(f"An error occurred in get_version: {str(e)}, {traceback.format_exc()}")
        return None

async def create_bridge_version(bridge_data, parent_id=None):
    bridge_version_data = bridge_data.copy()
    keys_to_remove = ['name', 'slugName', 'bridgeType', 'status']
    for key in keys_to_remove:
        if key in bridge_version_data:
            del bridge_version_data[key]
    bridge_version_data['is_drafted'] = True
    bridge_version_data['parent_id'] = parent_id or str(bridge_data['_id'])
    bridge_version_data['_id'] = ObjectId()
    await version_model.insert_one(bridge_version_data)
    return str(bridge_version_data['_id'])

async def update_bridges(bridge_id, update_fields):
    update_query = {}

    # Handle 'versions' separately with $addToSet
    if 'versions' in update_fields:
        update_query['$addToSet'] = {'versions': {'$each': update_fields.pop('versions')}}

    # Add remaining fields to $set
    if update_fields:
        update_query['$set'] = update_fields

    updated_bridge = await configurationModel.find_one_and_update(
        {'_id': ObjectId(bridge_id)},
        update_query,
        return_document=True,
        upsert=True
    )

    if not updated_bridge:
        raise BadRequestException('No records updated or bridge not found')


    if updated_bridge:
        updated_bridge['_id'] = str(updated_bridge['_id'])  # Convert ObjectId to string
        if 'function_ids' in updated_bridge and updated_bridge['function_ids'] is not None:
            updated_bridge['function_ids'] = [str(fid) for fid in updated_bridge['function_ids']]  # Convert function_ids to string
    return updated_bridge
    
async def get_version_with_tools(bridge_id, org_id):
    pipeline = [
        {
            '$match': {'_id': ObjectId(bridge_id), "org_id": org_id}
        },
        {
            '$lookup': {
                'from': 'apicalls',
                'localField': 'function_ids', 
                'foreignField': '_id',
                'as': 'apiCalls'
            }
        },
        {
            '$addFields': {
                '_id': {'$toString': '$_id'},
                'function_ids': {
                    '$map': {
                        'input': '$function_ids',
                        'as': 'fid',
                        'in': {'$toString': '$$fid'}
                    }
                },
                'apiCalls': {
                    '$arrayToObject': {
                        '$map': {
                            'input': '$apiCalls',
                            'as': 'api_call',
                            'in': {
                                'k': {'$toString': '$$api_call._id'},
                                'v': {
                                    '$mergeObjects': [
                                        '$$api_call',
                                        {
                                            '_id': {'$toString': '$$api_call._id'},
                                            'bridge_ids': {
                                                '$map': {
                                                    'input': '$$api_call.bridge_ids',
                                                    'as': 'bid',
                                                    'in': {'$toString': '$$bid'}
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    ]

    result = await version_model.aggregate(pipeline).to_list(length=None)
    
    if not result:
        raise BadRequestException('No matching records found')
    
    return {
        'success': True,
        'bridges': result[0]
    }
    
async def publish(org_id, version_id, user_id):
    get_version_data = (await get_bridges_with_tools(bridge_id = None, org_id = org_id, version_id = version_id)).get('bridges')
    if not get_version_data:
        raise BadRequestException('version data not found')
    
    parent_id = str(get_version_data.get('parent_id'))
    prompt = get_version_data.get('configuration',{}).get('prompt','')
    variable_state = get_version_data.get('variables_state', {})
    variable_path = get_version_data.get('variables_path', {})
    agent_variables = Helper.get_req_opt_variables_in_prompt(prompt, variable_state, variable_path)
    transformed_agent_variables = Helper.transform_agent_variable_to_tool_call_format(agent_variables)

    await delete_in_cache(f"{redis_keys['get_bridge_data_']}{parent_id}")

    if not parent_id:
        raise BadRequestException("Parent ID not found in version data")
    
    parent_configuration = await configurationModel.find_one({'_id': ObjectId(parent_id)})
    prev_published_version_id = parent_configuration.get('published_version_id')
    if not parent_configuration:
        raise BadRequestException("Parent configuration not found")
    
    published_version_id = str(get_version_data['_id'])
    get_version_data.pop('_id', None)
    updated_configuration = {**parent_configuration, **get_version_data}
    updated_configuration['published_version_id'] = published_version_id
    
    asyncio.create_task(makeQuestion(parent_id, updated_configuration.get("configuration",{}).get("prompt",""), updated_configuration.get('apiCalls'), save=True))
    asyncio.create_task(delete_current_testcase_history(version_id))
    # delete apicalls from updated_configuration
    del updated_configuration['apiCalls']
    
    if updated_configuration.get('function_ids'):
        updated_configuration['function_ids'] = [ObjectId(fid) for fid in updated_configuration['function_ids']]
    # updated_configuration['agent_variables'] = agent_variables
    updated_configuration['connected_agent_details'] = {
        **updated_configuration.get('connected_agent_details', {}), 
        'agent_variables' : {
            'fields' : transformed_agent_variables['fields'],
            'required_params' : transformed_agent_variables['required_params']
        }
    }
    
    
    await configurationModel.update_one(
        {'_id': ObjectId(parent_id)},
        {'$set': updated_configuration}
    )
    await version_model.update_one({'_id': ObjectId(prev_published_version_id)}, {'$set': {'is_drafted': True}})
    await version_model.update_one({'_id': ObjectId(published_version_id)}, {'$set': {'is_drafted': False}})
    await add_bulk_user_entries([{
                'user_id': user_id,
                'org_id': org_id,
                'bridge_id': parent_id,
                'version_id': version_id,
                "type": 'Version published'
            }])
    
    return {
        "success": True,
        "message": "Configuration updated successfully", 
    }
async def makeQuestion(parent_id, prompt, functions, save = False):
    if functions: 
        filtered_functions = {
            function['endpoint_name']: function['description'] for function in functions.values()
        }
        prompt += "\nFunctionalities available\n" + json.dumps(filtered_functions)
        
    
    expected_questions = await call_ai_middleware(prompt, bridge_id = bridge_ids['make_question'])
    updated_configuration= {"starterQuestion": expected_questions.get("questions",[])}
    
    # Update the document in the configurationModel
    if save: 
        configurationModel.update_one(  # this should be async
            {'_id': ObjectId(parent_id)},
            {'$set': updated_configuration}
        )
    return expected_questions
    

async def get_comparison_score(org_id, version_id):
    version_data = (await get_bridges_with_tools_and_apikeys(None, org_id, version_id))['bridges']
    published_version = (await get_bridges_without_tools(version_data['parent_id']))['bridges']
    
    version_data['apikey'] = Helper.decrypt(version_data['apikeys'][version_data['service']])
    
    response = None 
    
    timer = Timer()
    timer.start()

    if not published_version.get('expected_qna'):
        expected_questions = published_version.get('starterQuestion')
        if not expected_questions: 
            expected_questions = await makeQuestion(version_data['parent_id'], version_data.get('configuration').get('prompt'), version_data.get('apiCalls'))
        expected_answers_responses = await asyncio.gather(
            *[chat({'body': { **version_data,  'user': question }, 'path_params': { 'bridge_id': version_id }, 'state': {'is_playground': True, 'timer' : timer.getTime() }}) 
            for question in expected_questions]
        )
        expected_answers = [json.loads(response.__dict__['body'].decode('utf-8'))['response']['choices'][0]['message']['content'] for response in expected_answers_responses]
        response = [
            {'question': expected_questions[i], 'answer': expected_answers[i]} 
            for i in range(len(expected_questions))
        ]
        configurationModel.update_one(
            {'_id': ObjectId(published_version['_id'])},
            {'$set': {'expected_qna': response }}
        )
    
    else: 
        expected_questions, expected_answers = zip(*[(qna['question'], qna['answer']) for qna in published_version.get('expected_qna')])
        new_answer_responses = await asyncio.gather(
            *[chat({'body': { **version_data,  'user': question }, 'path_params': { 'bridge_id': version_id }, 'state': {'is_playground': True, 'timer' : timer.getTime() }}) 
            for question in expected_questions]
        )
        new_answers = [json.loads(response.__dict__['body'].decode('utf-8'))['response']['choices'][0]['message']['content'] for response in new_answer_responses]
        
        comparision_scores = []
        
        for i in range(len(expected_questions)):
            score = compute_cosine_similarity(expected_answers[i], new_answers[i])
            comparision_scores.append(score)
        
        response = [{ 'question' : expected_questions[i], 'expected_answer' : expected_answers[i], 'model_answer': new_answers[i], 'comparison_score': comparision_scores[i] }  for i in range(len(new_answers))]
        
    
    return response
