import asyncio
import pydash as _
from datetime import datetime
import json
import requests
import traceback
from ....db_services import metrics_service, ConfigurationServices as ConfigurationService
from .utils import validate_tool_call, fetch_axios, axios_work_js, tool_call_formatter, sendResponse
from src.configs.serviceKeys import ServiceKeys
from src.configs.modelConfiguration import ModelsConfig
from ..openAI.runModel import runModel
from ..anthrophic.antrophicModelRun import anthropic_runmodel
from ....configs.constant import service_name
from ..groq.groqModelRun import groq_runmodel

class BaseService:
    def __init__(self, params):
        self.customConfig = params.get('customConfig')
        self.configuration = params.get('configuration')
        self.apikey = params.get('apikey')
        self.variables = params.get('variables')
        self.user = params.get('user')
        self.tool_call = params.get('tools')
        self.startTime = params.get('startTime')
        self.org_id = params.get('org_id')
        self.bridge_id = params.get('bridge_id')
        self.bridge = params.get('bridge')
        self.thread_id = params.get('thread_id')
        self.model = params.get('model')
        self.service = params.get('service')
        self.req = params.get('req')
        self.modelOutputConfig = params.get('modelOutputConfig')
        self.playground = params.get('playground')
        self.template = params.get('template')
        self.response_format = params.get('response_format')

    async def axios_work(self, data, code, is_python=False):
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

    async def run_tool(self, response, modelOutputConfig, service):
        axios_instance, is_python, args = '', False, {}
        match service:
            case 'openai' | 'groq':
                tools_call = _.get(response, modelOutputConfig.get('tools'))[0]
                name = tools_call.get('function', {}).get('name')
                axios_instance, is_python = await fetch_axios(ConfigurationService, name)
                args = json.loads(tools_call['function'].get('arguments', '{}'))
            case 'anthropic':
                tools_call = response['content'][1]
                name = tools_call.get('name')
                axios_instance, is_python = await fetch_axios(ConfigurationService, name)
                args = tools_call.get('input', {})
            case _:
                return False
        
        api_response = await self.axios_work(args, axios_instance, is_python)
        return   {
                    'tool_call_id': tools_call['id'],
                    'role': 'tool',
                    'name': name,
                    'content': json.dumps(api_response),
                }

    def update_configration(self, response, function_response, configuration, modelOutputConfig, service):    
        match service:
            case 'openai' | 'groq' :
                configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [_.get(response, modelOutputConfig.get('tools'))[0]]})
                configuration['messages'].append(function_response)
            case 'anthropic':
                configuration['messages'].append({'role': 'assistant', 'content': response['content']})
                configuration['messages'].append({'role': 'user','content':[{"type":"tool_result",  
                                                 "tool_use_id": function_response['tool_call_id'],
                                                 "content": function_response['content']}]})
            case  _:
                pass
        return configuration

    async def function_call(self, configuration, sensitive_config, service, response, l=0, tools={}):
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
            sendResponse(response_format, data = {'function_call': True}, success = True)
        
        func_response_data = await self.run_tool(model_response, modelOutputConfig, service)
        tools[func_response_data['name']] = func_response_data['content']
        configuration = self.update_configration(model_response, func_response_data, configuration, modelOutputConfig, service)
        if not playground:
            sendResponse(response_format, data = {'function_call': True, 'success': True, 'message': 'Going to GPT'}, success=True)
        ai_response = await self.chats(configuration, apikey, service)
        ai_response['tools'] = tools
        return await self.function_call(configuration, sensitive_config, service, ai_response, l, tools)

    async def handle_failure(self, response):
        usage = {
            'service': self.service,
            'model': self.model,
            'orgId': self.org_id,
            'latency': datetime.now().timestamp() - self.startTime,
            'success': False,
            'error': response.get('error')
        }
        asyncio.create_task(metrics_service.create([usage], {
            'thread_id': self.thread_id,
            'user': self.user if self.user else json.dumps(self.tool_call),
            'message': "",
            'org_id': self.org_id,
            'bridge_id': self.bridge_id,
            'model': self.configuration.get('model'),
            'channel': 'chat',
            'type': "error",
            'actor': "user" if self.user else "tool"
        }))
        asyncio.create_task(sendResponse(self.response_format, data=response.get('error')))
# todo
    def update_model_response(self, model_response, functionCallRes={}):
        funcModelResponse = functionCallRes.get("modelResponse", {})
        match self.service:
            case 'openai' | 'groq' :
                self.total_tokens = _.get(model_response, self.modelOutputConfig['usage'][0]['total_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['total_tokens'],0)
                self.prompt_tokens = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'],0)
                self.completion_tokens = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['completion_tokens'],0)
                if funcModelResponse:
                    _.set_(model_response, self.modelOutputConfig['message'], _.get(funcModelResponse, self.modelOutputConfig['message']))
                    _.set_(model_response, self.modelOutputConfig['tools'], _.get(funcModelResponse, self.modelOutputConfig['tools']))
                _.set_(model_response, self.modelOutputConfig['usage'][0]['total_tokens'], self.total_tokens)
                _.set_(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens'], self.prompt_tokens)
                _.set_(model_response, self.modelOutputConfig['usage'][0]['completion_tokens'], self.completion_tokens)
            case 'anthropic':
                self.prompt_tokens = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'],0)
                self.completion_tokens = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['completion_tokens'],0)
                self.total_tokens = self.prompt_tokens + self.completion_tokens
                if funcModelResponse:
                    _.set_(model_response, self.modelOutputConfig['message'], _.get(funcModelResponse, self.modelOutputConfig['message']))
                # _.set_(model_response, 'content[1].text', _.get(funcModelResponse, 'content[0].text'))
                _.set_(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens'], self.prompt_tokens)
                _.set_(model_response, self.modelOutputConfig['usage'][0]['completion_tokens'], self.completion_tokens)
                # _.set_(model_response, self.modelOutputConfig['usage'][0]['total_tokens'], self.total_tokens)
            case  _:
                pass

    def calculate_usage(self, model_response):
        match self.service:
            case 'openai' | 'groq' :
                usage = {}
                usage["totalTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['total_tokens'])
                usage["inputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens'])
                usage["outputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['completion_tokens'])
                usage["expectedCost"] = (usage['inputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['input_cost']) + (usage['outputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['output_cost'])
            case 'anthropic':
                usage = {}
                usage["inputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens'])
                usage["outputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['completion_tokens'])
                usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
                # usage["expectedCost"] = (usage['inputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['input_cost']) + (usage['outputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['output_cost'])
            case  _:
                pass
        return usage

    def prepare_history_params(self, model_response, tools):
        return {
            'thread_id': self.thread_id,
            'user': self.user if self.user else json.dumps(self.tool_call),
            'message': _.get(model_response, self.modelOutputConfig['message']) if _.get(model_response, self.modelOutputConfig['tools']) else _.get(model_response, self.modelOutputConfig['message']),
            'org_id': self.org_id,
            'bridge_id': self.bridge_id,
            'model': self.configuration.get('model'),
            'channel': 'chat',
            'type': "assistant" if _.get(model_response, self.modelOutputConfig['message']) else "tool_calls",
            'actor': "user" if self.user else "tool",
            'tools': tools
        }
    
    def service_formatter(self, configuration : object, service : str ):
        try:
            new_config = {ServiceKeys[service].get(key, key): value for key, value in configuration.items()}
            if configuration.get('tools', '') :
                new_config['tool_choice'] = "auto"
                new_config['tools'] = tool_call_formatter(configuration, service)
            elif 'tool_choice' in configuration:
                del new_config['tool_choice']   
            return new_config
        except KeyError as e:
            print(f"Service key error: {e}")
            raise "Service key error: {e}"
        except Exception as e:
            print(f"An error occurred: {e}")
            raise "Service key error: {e}"
        
    async def chats(self, configuration, apikey, service):
        try:
            response = {}
            if service == service_name['openai']:
                response = await runModel(configuration, True, apikey)
            elif service == service_name['anthropic']:
                response = await anthropic_runmodel(configuration, apikey)
            elif service == service_name['groq']:
                response = await groq_runmodel(configuration, True, apikey)
            if not response['success']:
                return {
                    'success': False,
                    'error': response['error']
                }
            return {
                'success': True,
                'modelResponse': response['response']
            }
        except Exception as e:
            traceback.print_exc()
            print("chats error=>", e)
            return {
                'success': False,
                'error': str(e)
            }


