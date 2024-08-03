import asyncio
import pydash as _
from .groqChats import groq_chats
from ..createConversations import ConversationService
from ...utils.helper import Helper
from ....db_services import metrics_service
from ...utils.customRes import ResponseSender
from datetime import datetime
import json
from ...utils.helper import Helper
from ...utils.formatter.openaiFormatter import service_formatter
from ....configs.constant import service_name

class Groq:
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
    
    async def groq_handler(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation')).get('messages', [])
        self.customConfig["messages"] = [{"role": "system", "content": self.configuration['prompt']}] + conversation + ([{"role": "user", "content": self.user}] if self.user else (self.tool_call or [])) 
        self.customConfig = service_formatter(self.customConfig, service_name['groq'])
        groq_response = await groq_chats(self.customConfig, self.apikey)
        modelResponse = groq_response.get("modelResponse", {})
        print(modelResponse,"hiii this is groq")
        if not groq_response.get('success'):
            if not self.playground:
                usage = {
                    'service': self.service,
                    'model': self.model,
                    'orgId': self.org_id,
                    'latency': datetime.now().timestamp() - self.startTime,
                    'success': False,
                    'error': groq_response.get('error')
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
                asyncio.create_task(ResponseSender.sendResponse(self.response_format,data = groq_response.get('error')))
                if self.response_format['type'] != 'default':
                    return

            return {'success': False, 'error': groq_response.get('error')}
        
        usage = {}
        usage["totalTokens"] = _.get(modelResponse, self.modelOutputConfig['usage'][0]['total_tokens'])
        usage["inputTokens"] = _.get(modelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'])
        usage["outputTokens"] = _.get(modelResponse, self.modelOutputConfig['usage'][0]['completion_tokens'])
        usage["expectedCost"] = (usage['inputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['input_cost']) + (usage['outputTokens'] / 1000 * self.modelOutputConfig['usage'][0]['total_cost']['output_cost'])

        if not self.playground:
            historyParams = {
                'thread_id': self.thread_id,
                'user': self.user if self.user else json.dumps(self.tool_call),
                'message':_.get(modelResponse, self.modelOutputConfig['message']) == None if _.get(modelResponse, self.modelOutputConfig['tools']) else  _.get(modelResponse, self.modelOutputConfig['message']), #modelResponse.get(self.modelOutputConfig['message']) if modelResponse.get(self.modelOutputConfig['message']) else modelResponse.get(self.modelOutputConfig['tools']),
                'org_id': self.org_id,
                'bridge_id': self.bridge_id,
                'model': self.configuration.get('model'),
                'channel': 'chat',
                'type': "assistant" if _.get(modelResponse, self.modelOutputConfig['message']) else "tool_calls",
                'actor': "user" if self.user else "tool",
                'tools': tools
            }
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage}
