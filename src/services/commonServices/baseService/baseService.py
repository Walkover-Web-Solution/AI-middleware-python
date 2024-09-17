import asyncio
import pydash as _
from datetime import datetime
import json
import requests
import traceback
from collections import ChainMap
from ....db_services import metrics_service, ConfigurationServices as ConfigurationService
from .utils import validate_tool_call, axios_work, tool_call_formatter, sendResponse
from src.configs.serviceKeys import ServiceKeys
from src.configs.modelConfiguration import ModelsConfig
from ..openAI.runModel import runModel
from ..anthrophic.antrophicModelRun import anthropic_runmodel
from ....configs.constant import service_name
from ..groq.groqModelRun import groq_runmodel
from ....configs.constant import service_name

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


    async def run_tool(self, responses, service):
        codes_mapping = {}
        names = []
        
        match service:
            case 'openai' | 'groq':
                for tool_call in responses['choices'][0]['message']['tool_calls']:
                    name = tool_call['function']['name']
                    args = json.loads(tool_call['function']['arguments'])
                    codes_mapping[name] = {
                        'tool_call': tool_call,
                        'name': name,
                        'args': args
                    }
                    names.append(name)
            case 'anthropic':
                for tool_call in responses['content'][1:]:  # Skip the first item
                    name = tool_call['name']
                    args = tool_call['input']
                    codes_mapping[name] = {
                        'tool_call': tool_call,
                        'name': name,
                        'args': args
                    }
                    names.append(name)
            case _:
                return False, {}

        api_calls_response = await ConfigurationService.get_api_call_by_names(names, self.org_id)
        if(api_calls_response == []):
            print(names, self.org_id, "uanble to find function")
            raise ValueError("uanble to find function")
        async def process_code_and_service_data(api_call):
            axios_instance = api_call.get('code') or api_call.get('axios')
            is_python = api_call.get('is_python', False)
            name = api_call.get('function_name', api_call.get('endpoint',''))
            api_response = await axios_work(codes_mapping[name]['args'], axios_instance, is_python)
            response_data = {
                'tool_call_id': codes_mapping[name]['tool_call'].get('id'),
                'role': 'tool',
                'name': codes_mapping[name]['name'],
                'content': json.dumps(api_response),
            }
            return response_data, {response_data['tool_call_id']: response_data}

        try:
            responses = []
            mapping = {}
            tool_call_id_set = set()
            for api_call in api_calls_response['apiCalls']:
                response_data, response_mapping = await process_code_and_service_data(api_call)#to call directly using promise
                if response_data['tool_call_id'] not in tool_call_id_set:
                    tool_call_id_set.add(response_data['tool_call_id'])
                    responses.append(response_data)
                    mapping.update(response_mapping)
            return responses, mapping
        except Exception as error:
            print(f"Error in run_tool: {error}")
            raise error

    def update_configration(self, response, function_responses, configuration, mapping_response_data, service, tools):    
        if(service == 'anthropic'):
            configuration['messages'].append({'role': 'assistant', 'content': response['content']})
            configuration['messages'].append({'role': 'user','content':[]})

        for index, function_response in enumerate(function_responses):
            tools[function_response['name']] = function_response['content']
        
            match service:
                case 'openai' | 'groq' :
                    assistant_tool_calls = response['choices'][0]['message']['tool_calls'][index]
                    configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [assistant_tool_calls]})
                    tool_calls_id = assistant_tool_calls['id']
                    configuration['messages'].append(mapping_response_data[tool_calls_id])
                case 'anthropic':
                    ordered_json = {"type":"tool_result",  
                                                 "tool_use_id": function_response['tool_call_id'],
                                                 "content": function_response['content']}
                    configuration['messages'][-1]['content'].append(ordered_json)
                case  _:
                    pass
        return configuration, tools

    async def function_call(self, configuration, service, response, l=0, tools={}):
        if not response.get('success'):
            return {'success': False, 'error': response.get('error')}
        modelfunc = getattr(ModelsConfig, self.model.replace('-',"_").replace('.',"_"), None)
        modelObj = modelfunc()
        modelOutputConfig = modelObj['outputConfig']
        model_response = response.get('modelResponse', {})

        if validate_tool_call(modelOutputConfig, service, model_response) and l <= 3:
            l += 1
            # Continue with the rest of the logic here
        else:
            return response
        
        if not self.playground:
            asyncio.create_task(sendResponse(self.response_format, data = {'function_call': True}, success = True))
        
        func_response_data,mapping_response_data = await self.run_tool(model_response, service)
        configuration, tools = self.update_configration(model_response, func_response_data, configuration, mapping_response_data, service, tools)
        if not self.playground:
            asyncio.create_task(sendResponse(self.response_format, data = {'function_call': True, 'success': True, 'message': 'Going to GPT'}, success=True))
        ai_response = await self.chats(configuration, self.apikey, service)
        ai_response['tools'] = tools
        return await self.function_call(configuration, service, ai_response, l, tools)

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
            'tools': tools,
            'chatbot_message' : ""
        }
    
    def service_formatter(self, configuration : object, service : str ):
        try:
            new_config = {ServiceKeys[service].get(key, key): value for key, value in configuration.items()}
            if configuration.get('tools', '') :
                if service == service_name['anthropic']:
                    new_config['tool_choice'] =  {"type": "auto"}
                elif service == service_name['openai'] or service_name['groq']:
                    new_config['tool_choice'] = "auto"

                
                new_config['tools'] = tool_call_formatter(configuration, service)
            elif 'tool_choice' in configuration:
                del new_config['tool_choice']  
            if 'tools' in new_config and len(new_config['tools']) == 0:
                del new_config['tools'] 
            return new_config
        except Exception as e:
            print(f"An error occurred: {e}")
            raise ValueError(f"Service key error: {e.args[0]}")
        
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
                raise ValueError(response['error'])
            return {
                'success': True,
                'modelResponse': response['response']
            }
        except Exception as e:
            traceback.print_exc()
            print("chats error=>", e)
            raise ValueError(f"error occurs from openAi api {e.args[0]}")