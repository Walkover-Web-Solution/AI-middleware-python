import asyncio
import pydash as _
import json
import traceback
from config import Config
from ....db_services import metrics_service
from .utils import validate_tool_call, tool_call_formatter, sendResponse, make_code_mapping_by_service, process_data_and_run_tools
from src.configs.serviceKeys import ServiceKeys
from src.configs.modelConfiguration import ModelsConfig
from ..openAI.runModel import runModel
from ..anthrophic.antrophicModelRun import anthropic_runmodel
from ....configs.constant import service_name
from ..groq.groqModelRun import groq_runmodel
from ....configs.constant import service_name
from ..openAI.image_model import OpenAIImageModel
from concurrent.futures import ThreadPoolExecutor


executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

class BaseService:
    def __init__(self, params):
        self.customConfig = params.get('customConfig')
        self.configuration = params.get('configuration')
        self.apikey = params.get('apikey')
        self.variables = params.get('variables')
        self.user = params.get('user')
        self.tool_call = params.get('tools')
        self.org_id = params.get('org_id')
        self.bridge_id = params.get('bridge_id')
        self.bridge = params.get('bridge')
        self.thread_id = params.get('thread_id')
        self.sub_thread_id = params.get('sub_thread_id')
        self.model = params.get('model')
        self.service = params.get('service')
        self.modelOutputConfig = params.get('modelOutputConfig')
        self.playground = params.get('playground')
        self.template = params.get('template')
        self.response_format = params.get('response_format')
        self.execution_time_logs = params.get('execution_time_logs',{})
        self.timer = params.get('timer')
        self.func_tool_call_data = []
        self.variables_path = params.get('variables_path')
        self.message_id = params.get('message_id')
        self.bridgeType = params.get('bridgeType')
        self.reasoning_model = params.get('reasoning_model')
        self.memory = params.get('memory')
        self.type = params.get('type')
        self.token_calculator = params.get('token_calculator')
        self.apikey_object_id = params.get('apikey_object_id')
        self.image_data = params.get('images')
        self.tool_call_count = params.get('tool_call_count')
        self.text = params.get('text')
        self.tool_id_and_name_mapping = params.get('tool_id_and_name_mapping')
        self.batch = params.get('batch')
        self.webhook = params.get('webhook')
        self.name = params.get('name')
        self.org_name = params.get('org_name')
        self.send_error_to_webhook = params.get('send_error_to_webhook')


    def aiconfig(self):
        return self.customConfig

    async def run_tool(self, responses, service):
        codes_mapping, function_list = make_code_mapping_by_service(responses, service)
        if not self.playground:
            asyncio.create_task(sendResponse(self.response_format, data = {'function_call': True, 'Name': function_list}, success = True))
        codes_mapping = await self.replace_variables_in_args(codes_mapping)
        return await process_data_and_run_tools(codes_mapping, self.tool_id_and_name_mapping, self.org_id)


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
        if configuration.get('tool_choice') is not None and configuration['tool_choice'] not in ['auto', 'none', 'required']:
                configuration['tool_choice'] = 'auto'
        if validate_tool_call(modelOutputConfig, service, model_response) and l <= self.tool_call_count:
            l += 1
            
            # Continue with the rest of the logic here
        else:
            return response
        
        if not self.playground:
            self.token_calculator.calculate_usage(response.get('modelResponse'))
        func_response_data,mapping_response_data, tools_call_data = await self.run_tool(model_response, service)
        self.func_tool_call_data.append(tools_call_data)
        configuration, tools = self.update_configration(model_response, func_response_data, configuration, mapping_response_data, service, tools)
        if not self.playground:
            asyncio.create_task(sendResponse(self.response_format, data = {'function_call': True, 'success': True, 'message': 'Going to GPT'}, success=True))
        ai_response = await self.chats(configuration, self.apikey, service)
        ai_response['tools'] = tools
        return await self.function_call(configuration, service, ai_response, l, tools)

    async def handle_failure(self, response):
        latency = {
            "over_all_time" : self.timer.stop("Api total time") or "",
            "model_execution_time": sum(self.execution_time_logs.values()) or "",
            "execution_time_logs" : self.execution_time_logs or {}
        }
        usage = {
            'service': self.service,
            'model': self.model,
            'orgId': self.org_id,
            'latency': json.dumps(latency),
            'success': False,
            'error': response.get('error'),
            'apikey_object_id': self.apikey_object_id
        }
        await asyncio.gather(
            metrics_service.create([usage], {
                'thread_id': self.thread_id,
                'sub_thread_id': self.sub_thread_id,
                'user': self.user if self.user else json.dumps(self.tool_call),
                'message': "",
                'org_id': self.org_id,
                'bridge_id': self.bridge_id,
                'model': self.configuration.get('model'),
                'channel': 'chat',
                'type': "error",
                'actor': "user" if self.user else "tool",
                'message_id' : self.message_id
            }, None, self.send_error_to_webhook),
            sendResponse(self.response_format, data=response.get('error')),
            return_exceptions=True
        )
# todo
    def update_model_response(self, model_response, functionCallRes={}):
        funcModelResponse = functionCallRes.get("modelResponse", {})
        match self.service:
            case 'openai' | 'groq' | 'anthropic':
                usage_config = self.modelOutputConfig['usage'][0]

                def get_combined_tokens(key, default=0):
                    return (_.get(model_response, key, default) or 0) + (_.get(funcModelResponse, key, default) or 0)

                self.prompt_tokens = get_combined_tokens(usage_config['prompt_tokens'])
                self.completion_tokens = get_combined_tokens(usage_config['completion_tokens'])
                self.total_tokens = self.prompt_tokens + self.completion_tokens

                if self.service in ['openai', 'groq']:
                    cached_tokens_key = usage_config.get('cached_tokens', 0)
                    self.cached_tokens = get_combined_tokens(cached_tokens_key)
                    _.set_(model_response, cached_tokens_key, self.cached_tokens)

                if self.service == 'anthropic':
                    self.cache_creation_input_tokens = get_combined_tokens(usage_config.get('cache_creation_input_tokens', 0))
                    self.cache_read_input_tokens = get_combined_tokens(usage_config.get('cache_read_input_tokens', 0))
                    _.set_(model_response, usage_config.get('cache_creation_input_tokens', 0), self.cache_creation_input_tokens)
                    _.set_(model_response, usage_config.get('cache_read_input_tokens', 0), self.cache_read_input_tokens)

                if funcModelResponse:
                    _.set_(model_response, self.modelOutputConfig['message'], _.get(funcModelResponse, self.modelOutputConfig['message']))
                    if self.service in ['openai', 'groq']:
                        _.set_(model_response, self.modelOutputConfig['tools'], _.get(funcModelResponse, self.modelOutputConfig['tools']))

                # _.set_(model_response, usage_config['total_tokens'], self.total_tokens)
                _.set_(model_response, usage_config['prompt_tokens'], self.prompt_tokens)
                _.set_(model_response, usage_config['completion_tokens'], self.completion_tokens)
            case _:
                pass

    def calculate_usage(self, model_response):
        match self.service:
            case 'openai' | 'groq' :
                usage = {}
                usage["totalTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['total_tokens'])
                usage["inputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens'])
                usage["outputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['completion_tokens'])
                usage["cachedTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0].get('cached_tokens', 0))
            case 'anthropic':
                usage = {}
                usage["inputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['prompt_tokens'])
                usage["outputTokens"] = _.get(model_response, self.modelOutputConfig['usage'][0]['completion_tokens'])
                usage['cachingReadTokens'] = _.get(model_response,self.modelOutputConfig['usage'][0].get('cache_read_input_tokens',0))
                usage['cachedCreationInputTokens'] = _.get(model_response,self.modelOutputConfig['usage'][0].get('cache_creation_input_tokens',0))
                usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
            case  _:
                pass
        return usage
    def prepare_history_params(self, model_response, tools):
        return {
            'thread_id': self.thread_id,
            'sub_thread_id': self.sub_thread_id,
            'user': self.user if self.user else json.dumps(self.tool_call),
            'message': _.get(model_response, self.modelOutputConfig['message']) if _.get(model_response, self.modelOutputConfig.get('tools')) else _.get(model_response, self.modelOutputConfig['message']),
            'org_id': self.org_id,
            'bridge_id': self.bridge_id,
            'model': self.configuration.get('model'),
            'channel': 'chat',
            'type': "assistant" if _.get(model_response, self.modelOutputConfig['message']) else "tool_calls",
            'actor': "user" if self.user else "tool",
            'tools': tools,
            'chatbot_message' : "",
            'tools_call_data' : self.func_tool_call_data,
            'message_id' : self.message_id,
            'image_url' : model_response.get('data',[{}])[0].get('url', None),
            'revised_prompt' : model_response.get('data',[{}])[0].get('revised_prompt', None),
            'urls' : self.image_data,
            'AiConfig' : self.customConfig,
            "firstAttemptError" : model_response.get('firstAttemptError') or '',
            "annotations" : _.get(model_response, self.modelOutputConfig.get('annotations')) or [],
        }
    
    def service_formatter(self, configuration : object, service : str ):
        try:
            new_config = {ServiceKeys[service].get(self.type, ServiceKeys[service]['default']).get(key, key): value for key, value in configuration.items()}
            if configuration.get('tools', '') :
                if service == service_name['anthropic']:
                    new_config['tool_choice'] =  {"type": "auto"}
                elif service == service_name['openai'] or service_name['groq']:
                    if configuration.get('tool_choice'):
                        if configuration['tool_choice'] not in ['auto', 'none', 'required', 'default']:
                            new_config['tool_choice'] = {"type": "function", "function": {"name": configuration['tool_choice']}}
                        else:
                            new_config['tool_choice'] = configuration['tool_choice']
                new_config['tools'] = tool_call_formatter(configuration, service, self.variables, self.variables_path)
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
            loop = asyncio.get_event_loop()
            if service == service_name['openai']:
                response = await runModel(configuration, apikey, self.execution_time_logs, self.bridge_id, self.timer, self.message_id, self.org_id, self.name, self.org_name)
            elif service == service_name['anthropic']:
                response = await loop.run_in_executor(executor, lambda: asyncio.run(anthropic_runmodel(configuration, apikey, self.execution_time_logs, self.bridge_id, self.timer, self.name, self.org_name)))
            elif service == service_name['groq']:
                response = await groq_runmodel(configuration, apikey, self.execution_time_logs, self.bridge_id,  self.timer, self.name, self.org_name)
            if not response['success']:
                raise ValueError(response['error'], self.func_tool_call_data)
            return {
                'success': True,
                'modelResponse': response['response']
            }
        except Exception as e:
            traceback.print_exc()
            print("chats error=>", e)
            raise ValueError(f"error occurs from {self.service} api {e.args[0]}", *e.args[1:], self.func_tool_call_data)

    async def replace_variables_in_args(self, codes_mapping):
        variables = self.variables
        variables_path = self.variables_path
        if variables_path is None:
            return codes_mapping

        for key, value in codes_mapping.items():
            args = value.get('args')
            function_name = self.tool_id_and_name_mapping.get(value.get('name'), {}).get('name', value.get('name'))

            if args is not None and function_name in variables_path:
                function_variables_path = variables_path[function_name]
                for path_key, path_value in function_variables_path.items():
                    value_to_set = _.objects.get(variables, path_value)

                    if value_to_set is not None:
                        _.objects.set_(args, path_key, value_to_set)

                value['args'] = args

        return codes_mapping

    async def image(self, configuration, apikey, service):
        try:
            response = {}
            if service == service_name['openai']:
                response = await OpenAIImageModel(configuration, apikey, self.execution_time_logs, self.timer)
            if not response['success']:
                raise ValueError(response['error'])
            return {
                'success': True,
                'modelResponse': response['response']
            }
        except Exception as e:
            traceback.print_exc()
            print("chats error=>", e)
            raise ValueError(f"error occurs from {self.service} api {e.args[0]}")