from models.mongo_connection import db
configurationModel = db["configurations"]
from src.services.utils.testcase_utils import add_prompt_and_conversations
from src.services.commonServices.openAI.runModel import openai_test_model
from src.services.commonServices.anthrophic.antrophicModelRun import anthropic_test_model
from src.services.commonServices.groq.groqModelRun import groq_test_model
import pydash as _
from src.services.commonServices.baseService.utils import  makeFunctionName, make_code_mapping_by_service, validate_tool_call
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.testcase_services import get_testcases
from src.services.utils.common_utils import configure_custom_settings, load_model_configuration
import asyncio
import traceback
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id




async def run_testcase(testcase_data, parsed_data, function_names, given_custom_config, model_output_config):
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
                'tool_arguments' : None, 
                'expected_tool_arguments' : tool['arguments'],                
            } 
            for tool in testcase_data['expected']['tool_calls']
        }
        
        if not validate_tool_call(model_output_config, parsed_data['service'], result['response']):
            return testcase_result
        tool_call_response = make_code_mapping_by_service(result['response'], parsed_data['service']).values()
        expected_tool_calls = { tool_call['id'] : tool_call['arguments'] for tool_call in testcase_data['expected']['tool_calls']} 
        
        for tool_call in tool_call_response:
                tool_id = function_names.get(tool_call['name'])
                if not tool_id :
                    continue
                score = 1 if _.is_equal(tool_call['args'], expected_tool_calls[tool_id]) else 0
                testcase_result[tool_id]['score'] = score
                testcase_result[tool_id]['tool_arguments'] = tool_call['args']

        return testcase_result
    except Exception as error:
        traceback.print_exc()
        raise error


async def run_testcases(parsed_data, org_id, bridge_id):
    functions = await get_all_api_calls_by_org_id(org_id)
    function_names = {makeFunctionName(func['endpoint_name']): func['_id'] for func in functions}
        
    testcases_data = await get_testcases(bridge_id)

    # version_data = (await get_bridges_with_tools_and_apikeys(None, parsed_data['org_id'], version_id))['bridges']
    model_config, custom_config, model_output_config = await load_model_configuration(
        parsed_data['configuration']['model'], parsed_data['configuration']
    )
    custom_config = await configure_custom_settings(
        model_config['configuration'], custom_config, parsed_data['service']
    )
    
    tasks = [run_testcase(testcase, parsed_data, function_names, custom_config, model_output_config) for testcase in testcases_data]         
    result = await asyncio.gather(*tasks)
    response = {str(testcase['_id']) : { 'tool_call_result': testcase_result } for testcase, testcase_result in zip(testcases_data, result)}
    return response