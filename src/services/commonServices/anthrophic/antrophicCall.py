from ...utils.formatter.openaiFormatter import service_formatter
import pydash as _
from .antrophicChats import chats
import asyncio
from datetime import datetime
from ....db_services import metrics_service
import json
from ...utils.customRes import ResponseSender
from src.configs.constant import service_name
from ..openAI.functionCall import function_call

class Antrophic:
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
        self.bridge = params.get('bridge')
        self.apiCallavailable = True #bridge.get('is_api_call', False) if bridge is not None else False
        self.playground = params.get('playground')
        self.template = params.get('template')
        self.response_format = params.get('response_format')
    
    async def antrophic_handler(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = [] # create conversation according to claude models
        self.customConfig['system'] = self.configuration.get('prompt')
        self.customConfig["messages"] = [{"role": "user", "content":[{ "type": "text","text": self.user }]  }] + conversation
        self.customConfig['tools'] = self.tool_call
        self.customConfig = service_formatter(self.customConfig, service_name['anthropic'])
        antrophic_response = await chats(self.customConfig, self.apikey)
        modelResponse = antrophic_response.get("modelResponse", {})
        print(modelResponse,"antrophic_response")
        if not antrophic_response.get('success'):
            if not self.playground:
                usage = {
                    'service': self.service,
                    'model': self.model,
                    'orgId': self.org_id,
                    'latency': datetime.now().timestamp() - self.startTime,
                    'success': False,
                    'error': antrophic_response.get('error')
                }
                asyncio.create_task(metrics_service.create([usage], {
                    'thread_id': self.thread_id,
                    'user': self.user if self.user else json.dumps(self.tool_call),
                    'message': "",
                    'org_id': self.org_id,
                    'bridge_id': self.bridge_id,
                    'model': self.configuration.get('model'),
                    'channel': 'chat',
                    'type': "",
                    'actor': "user" if self.user else "tool"
                }))
                asyncio.create_task(ResponseSender.sendResponse(self.response_format,data = antrophic_response.get('error')))
                if self.response_format['type'] != 'default':
                    return

            return {'success': False, 'error': antrophic_response.get('error')}
        
        functionCallRes = await function_call(self.customConfig,{
                'apikey': self.apikey,
                'response_format' : self.response_format,
                'playground': self.playground,
            },service_name['anthropic'], antrophic_response)
        funcModelResponse = functionCallRes.get("modelResponse", {})
        tools = functionCallRes.get("tools", {})

        if not functionCallRes.get('success'):
                usage = {
                    'service': self.service,
                    'model': self.model,
                    'orgId': self.org_id,
                    'latency': datetime.now().timestamp() - self.startTime,
                    'success': False,
                    'error': functionCallRes.get('error')
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

                asyncio.create_task(ResponseSender.sendResponse(self.response_format, data = functionCallRes.get('error')))
                if self.response_format['type'] != 'default':
                    return

                return {'success': False, 'error': functionCallRes.get('error')}
        
        usage = {}
        usage["inputTokens"] = _.get(modelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'])
        usage["outputTokens"] = _.get(modelResponse, self.modelOutputConfig['usage'][0]['completion_tokens'])
        usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
        usage["expectedCost"] = (usage['inputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['input_cost']) + (usage['outputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['output_cost'])

        if not self.playground:
            historyParams = {
                'thread_id': self.thread_id,
                'user': self.user if self.user else json.dumps(self.tool_call),
                'message':_.get(modelResponse, self.modelOutputConfig['message']) == None if _.get(modelResponse, self.modelOutputConfig['tools']) else  _.get(modelResponse, self.modelOutputConfig['message']),
                'org_id': self.org_id,
                'bridge_id': self.bridge_id,
                'model': self.configuration.get('model'),
                'channel': 'chat',
                'type': "assistant" if _.get(modelResponse, self.modelOutputConfig['message']) else "tool_calls",
                'actor': "user" if self.user else "tool",
                'tools': tools
            }
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage}
        
