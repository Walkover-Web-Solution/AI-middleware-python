import pydash as _
from src.configs.modelConfiguration import ModelsConfig
from ..utils.customRes import ResponseSender
import asyncio
import json
import logging
import requests
import re
import pydash as _
from ...db_services import ConfigurationServices as ConfigurationService
def validate_tool_call(modelOutputConfig, service, response):
    match service:
        case 'openai':
            return True if _.get(response, modelOutputConfig.get('tools')) else False
        case 'groq':
            return False
        case 'gemini':
            return False
        case 'Claude':
            return False


async def fetch_axios(name):
    api_call = await ConfigurationService.get_api_call_by_name(name)
    axios_instance = api_call['apiCall'].get('code') or api_call['apiCall'].get('axios')  
    is_python = api_call['apiCall'].get('is_python', False)
    return axios_instance, is_python

async def axios_work(data, code, is_python=False):
    try:
        if not is_python:
            return await axios_work_js(data, code)
        
         # Append the execution code to the provided code
        exec_code = code + """
result =  axios_call(params)
"""
        # Prepare the environment for execution
        local_vars = {'params': data}
        global_vars = {"requests": requests, "asyncio": __import__('asyncio')}

        exec(exec_code, global_vars, local_vars)
        return {
            'response': local_vars.get('result'),
            'status': 1
        }
    except Exception as err:
        return {
            'response': '',
            'metadata':{
                'error': str(err),
            },
            'status': 0
        }

async def axios_work_js(data, axios_function):
    try:    
        pattern = pattern = r"https?:\/\/(flow\.sokt\.io|prod-flow-vm\.viasocket\.com)\/func\/([a-zA-Z0-9]+)"
        match = re.search(pattern, axios_function)
        script_id = match.group(2)
        response = requests.post(f"https://flow.sokt.io/func/{script_id}", json=data)
        return {
            'response': response.json(),
            'metadata':{
                'flowHitId': response.headers.get('flowHitId'),
            },
            'status': 1
        }
        
    except Exception as err:
        print("Error calling function=>", err)
        return {
            'response': '',
            'metadata':{
                'error': str(err),
            },
            'status': 0
        }

async def get_tool_configuration(response, modelOutputConfig, service):
    axios_instance, is_python, args = '', False, {}
    
    match service:
        case 'openai':
            tools_call = _.get(response, modelOutputConfig.get('tools'))[0]
            name = tools_call.get('function', {}).get('name')
            axios_instance, is_python = await fetch_axios(name)
            args = json.loads(tools_call['function'].get('arguments', '{}'))
        case 'groq' | 'gemini' | 'Claude':
            return False
    
    api_response = await axios_work(args, axios_instance, is_python)
    func_response_data = {
                'tool_call_id': tools_call['id'],
                'role': 'tool',
                'name': name,
                'content': json.dumps(api_response),
            }
    return func_response_data

# async def update_configration(configration,func_response_data,service):



async def function_call(configuration, service, response,l=0):
    modelfunc = getattr(ModelsConfig, configuration['model'], None)
    modelObj = modelfunc()
    modelOutputConfig = modelObj['outputConfig']

    if not (validate_tool_call(modelOutputConfig, service, response)):
       return response
    l+=1
    if not configuration['playground']:
        ResponseSender.sendResponse(configuration['response_format'], data = {'function_call': True}, success = True)
    
    func_response_data = await get_tool_configuration(response,modelOutputConfig, service)
    configuration['tools'][func_response_data['name']] = json.dumps(func_response_data['content'])
    configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [_.get(response, modelOutputConfig.get('tools'))[0]]})
    configuration['messages'].append(func_response_data)
    return func_response_data

    # try:
    #     configuration = data.get('configuration')
    #     apikey = data.get('apikey')
    #     bridge = data.get('bridge')
    #     tools_call = data.get('tools_call')
    #     output_config = data.get('outputConfig')
    #     playground = data.get('playground', False)
    #     tools = data.get('tools', {})
    #     api_endpoints =  set(bridge.get('api_endpoints', []))
    #     api_name = tools_call.get('function', {}).get('name')

    #     if api_name in api_endpoints:
    #         api_info = bridge['api_call'][api_name]
    #         axios_instance, is_python = await fetch_axios(api_info)
    #         args = json.loads(tools_call['function'].get('arguments', '{}'))
    #         api_response = await axios_work(args, axios_instance, is_python)
    #         func_response_data = {
    #             'tool_call_id': tools_call['id'],
    #             'role': 'tool',
    #             'name': api_name,
    #             'content': json.dumps(api_response),
    #         }
    #         tools[api_name] = json.dumps(api_response)
    #         configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [tools_call]})
    #         configuration['messages'].append(func_response_data)
    #         #  todo :: add function name also in the rtlayer          
    #         if not playground:
    #             ResponseSender.sendResponse(response_format, data = {'function_call': True, 'success': True, 'message': 'Going to GPT'}, success=True)

    #         open_ai_response = await chats(configuration, apikey)
    #         model_response = open_ai_response.get('modelResponse', {})
    #         open_ai_response['tools'] = tools

    #         if not open_ai_response.get('success'):
    #             return {'success': False, 'error': open_ai_response.get('error')}
    #         if _.get(model_response, output_config['tools']) and l <= 3:
    #             if not playground:
    #                 ResponseSender.sendResponse(response_format, data = {'function_call': True, 'success': True, 'message': 'sending the next function call'}, success=True)

    #             data['l'] = data['l'] + 1
    #             data['tools_call'] = _.get(model_response, output_config['tools'])[0]
    #             data['tools'] = tools
    #             return await function_call(data)

    #         return open_ai_response

    #     return {'success': False, 'error': 'endpoint does not exist'}

    # except Exception as error:
    #     logging.error("function call error:", exc_info=error)
    #     return {'success': False, 'error': str(error)}
