from src.db_services.conversationDbService import add_bulk_user_entries
from models.mongo_connection import db, client
from bson import ObjectId, errors
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
from typing import Dict, Set, Iterable, Optional

configurationModel = db["configurations"]
version_model = db['configuration_versions']
apiCallModel = db['apicalls']
apikeyCredentialsModel = db['apikeycredentials']
testcases_history_model = db['testcases_history']


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
    bridge_data = await get_bridges_without_tools(bridge_id = parent_id, org_id = org_id)
    previous_published_version_id = bridge_data.get('bridges', {}).get('published_version_id', None)
    await delete_in_cache(f"{redis_keys['bridge_data_with_tools_']}{parent_id}")

    if not parent_id:
        raise BadRequestException("Parent ID not found in version data")
    
    parent_configuration = await configurationModel.find_one({'_id': ObjectId(parent_id)})
    
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
    
    
    # Start a transaction for atomic updates with rollback capability
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                # Update configuration
                await configurationModel.update_one(
                    {'_id': ObjectId(parent_id)},
                    {'$set': updated_configuration},
                    session=session
                )
                
                # Update published version status
                await version_model.update_one(
                    {'_id': ObjectId(published_version_id)}, 
                    {'$set': {'is_drafted': False}},
                    session=session
                )
                
                # Update previous published version status only if it exists
                if previous_published_version_id:
                    await version_model.update_one(
                        {'_id': ObjectId(previous_published_version_id)}, 
                        {'$set': {'is_drafted': True}},
                        session=session
                    )
                
                # Commit transaction if all updates succeed
                await session.commit_transaction()
                
            except Exception as e:
                # Rollback transaction if any update fails
                await session.abort_transaction()
                logger.error(f"Transaction failed and rolled back: {str(e)}")
                raise BadRequestException(f"Failed to publish version: {str(e)}")
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


async def _cleanup_connected_agents(version_id: str, org_id: str) -> Dict[str, Set[str]]:
    """Remove references to the version from connected agent mappings across bridges and versions."""
    affected_ids: Dict[str, Set[str]] = {'versions': set(), 'bridges': set()}

    config_cursor = configurationModel.find(
        {
            'org_id': org_id,
            'connected_agents': {'$type': 'object'}
        },
        {'connected_agents': 1}
    )
    async for doc in config_cursor:
        connected_agents = doc.get('connected_agents') or {}
        filtered_agents = {
            name: info
            for name, info in connected_agents.items()
            if info.get('version_id') != version_id
        }
        if len(filtered_agents) != len(connected_agents):
            await configurationModel.update_one(
                {'_id': doc['_id']},
                {'$set': {'connected_agents': filtered_agents}}
            )
            affected_ids['bridges'].add(str(doc['_id']))

    version_cursor = version_model.find(
        {
            'org_id': org_id,
            'connected_agents': {'$type': 'object'}
        },
        {'connected_agents': 1}
    )
    async for doc in version_cursor:
        connected_agents = doc.get('connected_agents') or {}
        filtered_agents = {
            name: info
            for name, info in connected_agents.items()
            if info.get('version_id') != version_id
        }
        if len(filtered_agents) != len(connected_agents):
            await version_model.update_one(
                {'_id': doc['_id']},
                {'$set': {'connected_agents': filtered_agents}}
            )
            affected_ids['versions'].add(str(doc['_id']))

    return affected_ids


async def _cleanup_api_calls(version_id: str) -> Dict[str, Set[str]]:
    """Detach the version from API call documents and collect impacted bridge/version ids for cache invalidation."""
    impacted: Dict[str, Set[str]] = {'bridges': set(), 'versions': set()}
    lookup_query = {
        '$or': [
            {'version_ids': version_id}
        ]
    }

    cursor = apiCallModel.find(lookup_query, {'bridge_ids': 1, 'version_ids': 1})
    async for doc in cursor:
        for bridge_id in doc.get('bridge_ids') or []:
            impacted['bridges'].add(str(bridge_id))
        for vid in doc.get('version_ids') or []:
            impacted['versions'].add(str(vid))

    await apiCallModel.update_many(
        {'version_ids': version_id},
        {'$pull': {'version_ids': version_id}}
    )

    return impacted


async def _cleanup_apikey_credentials(version_id: str) -> None:
    """Remove the version from any apikey credential mappings."""
    await apikeyCredentialsModel.update_many(
        {'version_ids': version_id},
        {'$pull': {'version_ids': version_id}}
    )


def _collect_rag_cache_keys(version_doc: dict) -> Set[str]:
    """Build cache keys tied to RAG resources associated with the version."""
    cache_keys: Set[str] = set()
    doc_ids = version_doc.get('doc_ids') or []
    for doc_id in doc_ids:
        if isinstance(doc_id, str):
            cache_keys.add(f"{redis_keys['files_']}{doc_id}")
    return cache_keys


async def _cleanup_testcase_history(version_id: str) -> None:
    """Drop testcase history documents linked to the version."""
    await testcases_history_model.delete_many({'version_id': version_id})


def _merge_impacted_ids(*impacts: Optional[Dict[str, Set[str]]]) -> Dict[str, Set[str]]:
    """Merge multiple impacted-id maps into a single structure."""
    merged: Dict[str, Set[str]] = {'bridges': set(), 'versions': set()}
    for impact in impacts:
        if not impact:
            continue
        merged['bridges'].update(impact.get('bridges', set()))
        merged['versions'].update(impact.get('versions', set()))
    return merged


def _build_cache_keys(
    version_id: str,
    parent_id: Optional[str],
    impacted_ids: Dict[str, Set[str]],
    extra_keys: Iterable[str]
) -> Set[str]:
    """Collect all Redis keys that should be cleared after removing the version."""
    cache_keys: Set[str] = {
        f"{redis_keys['get_bridge_data_']}{version_id}",
        f"{redis_keys['bridge_data_with_tools_']}{version_id}"
    }

    if parent_id:
        cache_keys.update({
            f"{redis_keys['get_bridge_data_']}{parent_id}",
            f"{redis_keys['bridge_data_with_tools_']}{parent_id}"
        })

    for bridge_id in impacted_ids['bridges']:
        cache_keys.update({
            f"{redis_keys['get_bridge_data_']}{bridge_id}",
            f"{redis_keys['bridge_data_with_tools_']}{bridge_id}"
        })

    for version in impacted_ids['versions']:
        cache_keys.update({
            f"{redis_keys['get_bridge_data_']}{version}",
            f"{redis_keys['bridge_data_with_tools_']}{version}"
        })

    cache_keys.update(extra_keys)
    return cache_keys


async def delete_bridge_version(org_id: str, version_id: str):
    if not version_id:
        raise BadRequestException("Invalid version id provided")

    version_doc = await version_model.find_one({'_id': ObjectId(version_id), 'org_id': org_id})
    if not version_doc:
        raise BadRequestException("Version not found")

    parent_id = version_doc.get('parent_id')
    parent_object_id = None
    if parent_id:
        try:
            parent_object_id = ObjectId(parent_id)
        except (errors.InvalidId, TypeError):
            parent_object_id = None

    if parent_object_id:
        parent_config = await configurationModel.find_one(
            {'_id': parent_object_id, 'org_id': org_id},
            {'published_version_id': 1}
        )
        if parent_config and parent_config.get('published_version_id') == version_id:
            raise BadRequestException("Cannot delete the currently published version. Publish a different version first.")

    connected_agents_impacted = await _cleanup_connected_agents(version_id, org_id)

    if parent_object_id:
        await configurationModel.update_one(
            {'_id': parent_object_id},
            {'$pull': {'versions': version_id}}
        )

    api_calls_impacted = await _cleanup_api_calls(version_id)
    await _cleanup_apikey_credentials(version_id)
    await _cleanup_testcase_history(version_id)

    delete_result = await version_model.delete_one({'_id': ObjectId(version_id), 'org_id': org_id})
    if delete_result.deleted_count == 0:
        raise BadRequestException("Failed to delete version")

    rag_cache_keys = _collect_rag_cache_keys(version_doc)
    impacted_ids = _merge_impacted_ids(connected_agents_impacted, api_calls_impacted)
    cache_keys_to_delete = _build_cache_keys(version_id, parent_id, impacted_ids, rag_cache_keys)

    if cache_keys_to_delete:
        await delete_in_cache(list(cache_keys_to_delete))

    return {
        "success": True,
        "message": "Version deleted successfully"
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

async def get_all_connected_agents(id: str, org_id: str, type: str):
    """
    Recursively finds all connected agents for a given bridge_id or version_id.
    Returns a structured map of agents with their parent-child relationships.
    """
    agents_map = {}
    visited = set()
    
    async def fetch_document(doc_id: str, doc_type: str = None):
        """Fetch document from either configurations or configuration_versions"""
        # If doc_type is specified, use it directly
        if doc_type == 'bridge':
            doc = await configurationModel.find_one({'_id': ObjectId(doc_id), 'org_id': org_id})
            if doc:
                return doc, 'bridge'
        elif doc_type == 'version':
            doc = await version_model.find_one({'_id': ObjectId(doc_id), 'org_id': org_id})
            if doc:
                return doc, 'version'
        else:
            doc = await configurationModel.find_one({'_id': ObjectId(doc_id), 'org_id': org_id})
            return doc, 'bridge'
        return None, None
    
    async def process_agent(agent_id: str, parent_ids: list = None, doc_type: str = None):
        """Recursively process an agent and its connected agents"""
        if agent_id in visited:
            # If already visited, just update parent relationship
            if parent_ids:
                for parent_id in parent_ids:
                    if parent_id not in agents_map[agent_id]['parentAgents']:
                        agents_map[agent_id]['parentAgents'].append(parent_id)
            return
        
        visited.add(agent_id)
        
        # Fetch the agent document
        doc, doc_type = await fetch_document(agent_id, doc_type)
        if not doc:
            return
        
        # Initialize agent in map
        agent_name = doc.get('name', f'Agent_{agent_id}')
        connected_agent_details = doc.get('connected_agent_details', {})
        thread_id = connected_agent_details.get('thread_id', False) if isinstance(connected_agent_details, dict) else False
        description = connected_agent_details.get('description') if isinstance(connected_agent_details, dict) else None
        
        agents_map[agent_id] = {
            'agent_name': agent_name,
            'parentAgents': parent_ids if parent_ids else [],
            'childAgents': [],
            'thread_id': thread_id
        }
        
        # Add description if available
        if description:
            agents_map[agent_id]['description'] = description
        
        # Process connected agents
        connected_agents = doc.get('connected_agents', {})
        if isinstance(connected_agents, dict):
            for agent_name_key, agent_info in connected_agents.items():
                if not isinstance(agent_info, dict):
                    continue
                
                # Check for bridge_id or version_id in connected agent
                child_id = agent_info.get('version_id') or agent_info.get('bridge_id')
                if child_id:
                    # Add to current agent's children
                    if child_id not in agents_map[agent_id]['childAgents']:
                        agents_map[agent_id]['childAgents'].append(child_id)
                    
                    # Determine child type based on which ID is present
                    child_type = 'version' if agent_info.get('version_id') else 'bridge'
                    
                    # Recursively process the child agent
                    await process_agent(child_id, [agent_id], child_type)
    
    # Start processing from the initial id
    await process_agent(id, None, type)
    
    return agents_map
