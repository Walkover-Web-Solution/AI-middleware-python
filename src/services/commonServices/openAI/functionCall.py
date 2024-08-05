import pydash as _
from src.configs.modelConfiguration import ModelsConfig
from src.services.commonServices.openAI.chat import chats
from ...utils.customRes import ResponseSender
import asyncio
import json
import logging
import requests
import re
import pydash as _
from ....db_services import ConfigurationServices as ConfigurationService
def validate_tool_call(modelOutputConfig, service, response):
    match service:
        case 'openai':
            return True if _.get(response, modelOutputConfig.get('tools')) else False
        case 'groq':
            return False
        case 'gemini':
            return False
        case 'anthropic':
            return True if response['stop_reason']=='tool_use'  else False


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

async def run_tool(response, modelOutputConfig, service):
    axios_instance, is_python, args = '', False, {}
    
    match service:
        case 'openai':
            tools_call = _.get(response, modelOutputConfig.get('tools'))[0]
            name = tools_call.get('function', {}).get('name')
            axios_instance, is_python = await fetch_axios(name)
            args = json.loads(tools_call['function'].get('arguments', '{}'))
        case 'anthropic':
            tools_call = response['content'][1]
            name = tools_call.get('name')
            axios_instance, is_python = await fetch_axios(name)
            args = tools_call.get('input', {})
        case 'groq' | 'gemini':
            return False
    
    api_response = await axios_work(args, axios_instance, is_python)
    func_response_data = {
                'tool_call_id': tools_call['id'],
                'role': 'tool',
                'name': name,
                'content': json.dumps(api_response),
            }
    return func_response_data

def update_configration(response, function_response, configuration, modelOutputConfig, service):    
    match service:
        case 'openai':
            configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [_.get(response, modelOutputConfig.get('tools'))[0]]})
            configuration['messages'].append(function_response)
        case 'anthropic':
            configuration['messages'].append({'role': 'assistant', 'content': response['content']})
            configuration['messages'].append({'role': 'user','content':[{"type":"tool_result",  
                                             "tool_use_id": function_response['tool_call_id'],
                                             "content": function_response['content']}]})
        case 'groq' | 'gemini':
            configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [_.get(response, modelOutputConfig.get('tools'))[0]]})
            configuration['messages'].append(function_response)
    return configuration

async def function_call(configuration,sensitive_config, service, response, l=0, tools={}):
    if not response.get('success'):
        return {'success': False, 'error': response.get('error')}
    modelfunc = getattr(ModelsConfig, configuration['model'].replace('-',"_").replace('.',"_"), None)
    modelObj = modelfunc()
    modelOutputConfig = modelObj['outputConfig']
    model_response = response.get('modelResponse', {})
    response_format=sensitive_config['response_format']
    playground=sensitive_config['playground']
    apikey = sensitive_config['apikey']


    if not (validate_tool_call(modelOutputConfig, service, model_response) and l <= 3):
       return response
    
    l+=1

    if not playground:
        ResponseSender.sendResponse(response_format, data = {'function_call': True}, success = True)
    
    func_response_data = await run_tool(model_response, modelOutputConfig, service)
    tools[func_response_data['name']] = func_response_data['content']
    configuration = update_configration(model_response, func_response_data, configuration, modelOutputConfig, service)
    if not playground:
        ResponseSender.sendResponse(response_format, data = {'function_call': True, 'success': True, 'message': 'Going to GPT'}, success=True)
    ai_response = await chats(configuration, apikey, service)
    ai_response['tools'] = tools
    return await function_call(configuration, sensitive_config, service, ai_response, l, tools)