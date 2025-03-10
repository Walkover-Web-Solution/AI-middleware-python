from models.mongo_connection import db
configurationModel = db["configurations"]
from src.services.utils.testcase_utils import add_prompt_and_conversations, MakeConversationsAsPerService
from src.services.commonServices.openAI.runModel import openai_test_model
from src.services.commonServices.anthrophic.antrophicModelRun import anthropic_test_model
from src.services.commonServices.groq.groqModelRun import groq_test_model
import pydash as _
from src.services.commonServices.baseService.utils import  makeFunctionName, make_code_mapping_by_service, validate_tool_call
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.testcase_services import get_testcases, create_testcases_history
from src.services.utils.common_utils import configure_custom_settings, load_model_configuration
import asyncio
import traceback
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from datetime import datetime
from itertools import chain
from src.services.utils.time import Timer
from src.services.utils.helper import Helper
from src.services.utils.nlp import compute_cosine_similarity
from src.services.utils.ai_call_util import call_ai_middleware
# from ..utils.ai_middleware_format import Response_formatter
import json



async def run_testcase_for_tools(testcase_data, parsed_data, function_names, given_custom_config, model_output_config):
    try:
        conversations =  testcase_data['conversation']
        custom_config = add_prompt_and_conversations(given_custom_config, conversations, parsed_data['service'], parsed_data['configuration']['prompt'])  
        apikey = parsed_data['apikey']
        result = None
        match parsed_data['service']:
            case 'openai': 
                result = await openai_test_model(custom_config, apikey)
            case 'groq' : 
                result = await groq_test_model(custom_config, apikey)  
            case 'anthropic' : 
                result = await anthropic_test_model(custom_config, apikey)   
        
        # tool_call_response = extract_tool_call(parsed_data['service'], result['response'])
        # if not result['response']['choices'][0]['message']['tool_calls']
        testcase_result = {
            tool['id']: {
                'model_output' : tool['arguments'],    
                'bridge_id' : parsed_data['bridge_id'], 
                'version_id' : parsed_data['version_id'],
                'created_at' : datetime.now().isoformat(), 
                'testcase_id' : str(testcase_data['_id']),
                'metadata' : {
                    'system_prompt' : parsed_data['body']['configuration']['prompt'], 
                    'model' : given_custom_config['model']
                }, 
            } 
            for tool in testcase_data['expected']['tool_calls']
        }
        
        if not validate_tool_call(model_output_config, parsed_data['service'], result['response']):
            return testcase_result
        tool_call_response, function_Calls_ignore = make_code_mapping_by_service(result['response'], parsed_data['service'])
        tool_call_response = list(tool_call_response.values())
        expected_tool_calls = { tool_call['id'] : tool_call['arguments'] for tool_call in testcase_data['expected']['tool_calls']} 
        
        total_score = 0
        for tool_call in tool_call_response:
                tool_id = function_names.get(tool_call['name'])
                if not tool_id :
                    continue
                score = 1 if _.is_equal(tool_call['args'], expected_tool_calls[tool_id]) else 0
                testcase_result[tool_id]['score'] = score if testcase_data['matching_type'] == 'exact' else await calculate_score(testcase_data['expected']['tool_calls'], tool_call_response, testcase_data['matching_type'], testcase_data['type'])
                testcase_result[tool_id]['model_output'] = tool_call['args']
                total_score += score
        
        # if testcase_data['matching_type'] != 'exact' : 
        #     testcase_result['score'] =  await calculate_score(testcase_data['expected']['tool_calls'], tool_call_response, testcase_data['matching_type'], testcase_data['type'])
        # else:     
        #     testcase_result['score'] =  total_score / len(tool_call_response)
        return testcase_result
    except Exception as error:
        traceback.print_exc()
        raise error


async def run_testcases(parsed_data, org_id, bridge_id, chat):
    functions = await get_all_api_calls_by_org_id(org_id)
    function_names = {makeFunctionName(func['endpoint_name'] or func['function_name']): func['_id'] for func in functions}
        
    testcases_data = await get_testcases(bridge_id)
    # version_data = (await get_bridges_with_tools_and_apikeys(None, parsed_data['org_id'], version_id))['bridges']
    model_config, custom_config, model_output_config = await load_model_configuration(
        parsed_data['configuration']['model'], parsed_data['configuration']
    )
    custom_config = await configure_custom_settings(
        model_config['configuration'], custom_config, parsed_data['service']
    )
    
    tasks = [run_testcase_for_tools(testcase, parsed_data, function_names, custom_config, model_output_config) for testcase in testcases_data if testcase['type'] == 'function']         
    tasks1 = [run_testcase_for_response(testcase, parsed_data, custom_config, model_output_config, chat) for testcase in testcases_data if testcase['type'] == 'response']         
    result = await asyncio.gather(*tasks, *tasks1)
    response = {str(testcase['_id']) : { 'result': testcase_result } for testcase, testcase_result in zip(testcases_data, result)}
    to_insert = list(chain.from_iterable(item.values() for item in result))
    print(to_insert)
    await create_testcases_history(to_insert)
    return response


async def run_testcase_for_response(testcase_data, parsed_data, given_custom_config, model_output_config, chat):
        
    timer = Timer()
    timer.start()
    parsed_data['configuration']['conversation'] = MakeConversationsAsPerService(testcase_data['conversation'][:-1], parsed_data['service'])
    result = await chat({'body': { **parsed_data, 'user' : testcase_data['conversation'][-1]['content']}, 'path_params': { 'bridge_id': parsed_data['version_id'] }, 'state': {'is_playground': True, 'timer' : timer.getTime() , 'version': 2}}) 
    response = json.loads(result.__dict__['body'].decode('utf-8'))['response']['data']['content']
    
    testcase_result = {    
        str(testcase_data['_id']): {
            'bridge_id' : parsed_data['bridge_id'], 
            'version_id' : parsed_data['version_id'],
            'created_at' : datetime.now().isoformat(), 
            'testcase_id' : str(testcase_data['_id']),
            'metadata' : {
                'system_prompt' : parsed_data['body']['configuration']['prompt'], 
                'model' : given_custom_config['model']
            }, 
        }    
    }


    # testcase_result[str(testcase_data['_id'])]['score'] = compute_cosine_similarity(testcase_data['expected']['response'], response)
    testcase_result[str(testcase_data['_id'])]['score'] = await calculate_score(testcase_data['expected']['response'], response, testcase_data['matching_type'], testcase_data['type'])
    testcase_result[str(testcase_data['_id'])]['model_output'] = response
    
    
    return testcase_result


async def calculate_score(expected, actual, matching_type, response_type): 
    match matching_type : 
        case 'cosine': 
            expected = json.dumps(expected) if isinstance(expected, dict) else str(expected)
            actual = json.dumps(actual) if isinstance(actual, dict) else str(actual)
            return compute_cosine_similarity(expected, actual)
        case 'exact' : 
            return _.is_equal(actual, expected)
        case 'ai' : 
            return await check_score_with_ai(expected, actual)
    

async def check_score_with_ai(expected, actual):
    response = json.loads(await call_ai_middleware(actual, '67ce993c8407023ad4f7b277', variables = {'expected' : expected }))['score']
    print(response)