from models.mongo_connection import db
configurationModel = db["configurations"]
from src.services.utils.testcase_utils import add_prompt_and_conversations, make_conversations_as_per_service
from src.services.cache_service import make_json_serializable
from src.services.commonServices.openAI.runModel import openai_test_model
from src.services.commonServices.anthrophic.antrophicModelRun import anthropic_test_model
from src.services.commonServices.groq.groqModelRun import groq_test_model
from src.services.commonServices.openRouter.openRouter_modelrun import openrouter_test_model
from src.services.commonServices.Mistral.mistral_model_run import mistral_test_model
from src.services.commonServices.Google.gemini_modelrun import gemini_test_model
from src.services.commonServices.AiMl.ai_ml_model_run import ai_ml_test_model
import pydash as _
from src.services.commonServices.baseService.utils import  makeFunctionName, make_code_mapping_by_service, validate_tool_call
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.testcase_services import get_testcases, create_testcases_history, get_testcases_using_id
from src.services.utils.common_utils import configure_custom_settings, load_model_configuration
import asyncio
import traceback
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from datetime import datetime
from itertools import chain
from src.services.utils.time import Timer
from src.services.utils.helper import Helper
from src.services.utils.nlp import compute_cosine_similarity
import json
from src.services.utils.ai_call_util import call_ai_middleware
from src.services.utils.ai_middleware_format import Response_formatter
from src.configs.constant import bridge_ids


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
            case 'open_router':
                result = await openrouter_test_model(custom_config, apikey)
            case 'mistral':
                result = await mistral_test_model(custom_config, apikey)
            case 'gemini':
                result = await gemini_test_model(custom_config, apikey)
            case 'ai_ml':
                result = await ai_ml_test_model(custom_config, apikey)   
                
        # Handle both success and error cases
        if result and result.get('success'):
            return result['response']
        else:
            # Log the error and return None or empty response
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"Test model call failed: {error_msg}")
            return None


    except Exception as error:
        traceback.print_exc()
        return False


async def run_bridge_testcases(parsed_data, org_id, bridge_id, testcase_id = None):
    functions = await get_all_api_calls_by_org_id(org_id)
    function_names = {makeFunctionName(func['endpoint_name'] or func['function_name']): func['_id'] for func in functions}
    if testcase_id:
        testcases_data = await get_testcases_using_id(testcase_id)
    else:    
        testcases_data = await get_testcases(bridge_id)
    # version_data = (await get_bridges_with_tools_and_apikeys(None, parsed_data['org_id'], version_id))['bridges']
    model_config, custom_config, model_output_config = await load_model_configuration(
        parsed_data['configuration']['model'], parsed_data['configuration'], parsed_data['service'], 
    )
    custom_config = await configure_custom_settings(
        model_config['configuration'], custom_config, parsed_data['service']
    )
    
    tasks = [
        run_testcase_for_tools(testcase, parsed_data, function_names, custom_config, model_output_config)
        # if testcase['type'] == 'function'
        # else run_testcase_for_response(testcase, parsed_data, chat)
        for testcase in testcases_data
    ]
    result = await asyncio.gather(*tasks)
    expected_answers = [extract_tool_response(res, model_output_config, parsed_data['service']) if testcase['type'] == 'function' else await extract_response(res, parsed_data['service']) for res, testcase in zip(result, testcases_data )]
    data_to_insert = [{
            'bridge_id' : parsed_data['bridge_id'], 
            'version_id' : parsed_data['version_id'],
            'created_at' : datetime.now().isoformat(), 
            'testcase_id' : str(testcase_data['_id']),
            'metadata' : {
                'system_prompt' : parsed_data['body']['configuration']['prompt'], 
                'model' : custom_config['model']
            }, 
            'model_output' : test_result, 
            'score' : await compare_result(testcase_data['expected']['response' if testcase_data['type'] == 'response' else 'tool_calls'], test_result, testcase_data['matching_type'], testcase_data['type'])
    } for testcase_data, test_result in zip(testcases_data, expected_answers)]
    
    response = {str(testcase['_id']) : { **make_json_serializable(testcase), **{'result': testcase_result} } for testcase, testcase_result in zip(testcases_data, data_to_insert) }
    await create_testcases_history(data_to_insert)
    return response


def extract_tool_response(response, model_output_config, service):
    if not validate_tool_call(model_output_config, service, response):
        return None
        
    tool_call_response, function_list  = make_code_mapping_by_service(response, service)
    tool_call_response = list(tool_call_response.values())
    return tool_call_response

async def extract_response(response, service):
    if not response : 
        return ''
    response = await Response_formatter(response = response, service = service)
    # response = json.loads(response.__dict__[' body'].decode('utf-8'))['response']['data']['content']
    
    return response['data'].get('content', '')

async def run_testcase_for_response(testcase_data, parsed_data, chat):
    timer = Timer()
    timer.start()
    parsed_data['configuration']['conversation'] = testcase_data['conversation'][:-1]
    parsed_data['configuration']['conversation'] = make_conversations_as_per_service(testcase_data['conversation'][:-1], parsed_data['service'])
    result = await chat({'body': { **parsed_data, 'user' : testcase_data['conversation'][-1]['content']}, 'path_params': { 'bridge_id': parsed_data['version_id'] }, 'state': {'is_playground': True, 'timer' : timer.getTime() , 'version': 2}}) 
    response = json.loads(result.__dict__['body'].decode('utf-8'))['response']['data']['content']
    return response


async def compare_result(expected, actual, matching_type, response_type):
    if(response_type == 'function'):
        expected = {case['name'] : case.get('arguments', {}) for case in expected}
        actual = {case['name'] : case['args'] for case in actual or []}
    match matching_type: 
        case 'cosine' : 
            expected = str(expected)
            actual = str(actual)
            return compute_cosine_similarity(expected, actual)
        case 'exact': 
                return 1 if _.is_equal(expected, actual) else 0
        case 'ai' : 
            response =  await call_ai_middleware(str(actual), bridge_ids['compare_result'], variables = ({'expected' : str(expected) }))
            return response['score']
        