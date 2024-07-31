import asyncio
import pydash as _
from .chat import chats
from ..createConversations import ConversationService
from ...utils.helper import Helper
from ....db_services import metrics_service
from .functionCall import function_call
from ...utils.customRes import ResponseSender
from datetime import datetime
import json
from ...utils.helper import Helper

class UnifiedOpenAICase:
    def __init__(self, params):
        self.customConfig = params.get('customConfig')
        self.configuration = params.get('configuration')
        self.apikey = params.get('apikey')
        self.variables = params.get('variables')
        self.user = params.get('user')
        self.tool_call = params.get('tool_call')
        self.startTime = params.get('startTime')
        self.org_id = params.get('org_id')
        self.bridge_id = params.get('bridge_id')
        self.bridge = params.get('bridge')
        self.thread_id = params.get('thread_id')
        self.model = params.get('model')
        self.service = params.get('service')
        self.rtlLayer = params.get('rtlayer')
        self.req = params.get('req')
        self.modelOutputConfig = params.get('modelOutputConfig')
        self.bridge = params.get('bridge')
        self.apiCallavailable = True #bridge.get('is_api_call', False) if bridge is not None else False
        self.playground = params.get('playground')
        self.RTLayer = params.get('RTLayer')
        self.webhook = params.get('webhook')
        self.headers = params.get('headers')
        self.template = params.get('template')
        self.prompt = params.get('prompt')
        self.input = params.get('input')

    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        prompt = self.configuration.get('prompt', [])
        prompt = prompt if isinstance(prompt, list) else [prompt]
        conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation')).get('messages', [])
        prompt = Helper.replace_variables_in_prompt(prompt, self.variables)
        if self.template:
            system_prompt = [{"role": "system", "content": self.template}]
            prompt = Helper.replace_variables_in_prompt(system_prompt, {"system_prompt": prompt[0].get('content'), **self.variables})

        self.customConfig["messages"] = prompt + conversation + ([{"role": "user", "content": self.user}] if self.user else (self.tool_call or [])) 
        openAIResponse = await chats(self.customConfig, self.apikey)
        modelResponse = openAIResponse.get("modelResponse", {})

        if not openAIResponse.get('success'):
            if not self.playground:
                usage = {
                    'service': self.service,
                    'model': self.model,
                    'orgId': self.org_id,
                    'latency': datetime.now().timestamp() - self.startTime,
                    'success': False,
                    'error': openAIResponse.get('error')
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
                asyncio.create_task(ResponseSender.sendResponse(
                    rtl_layer = self.rtlLayer,
                    webhook= self.webhook,
                    data= {'error': openAIResponse.get('error'), 'success': False},
                    req_body=  await self.req.json() if self.req else {},
                    headers= self.headers or {}
                ))
                if self.rtlLayer or self.webhook:
                    return

            return {'success': False, 'error': openAIResponse.get('error')}
        if _.get(modelResponse, self.modelOutputConfig.get('tools')) and self.apiCallavailable:
            if not self.playground:
                ResponseSender.sendResponse({
                    'rtlLayer': self.rtlLayer,
                    'webhook': self.webhook,
                    'data': {'function_call': True, 'success': True},
                    'reqBody': self.req.json if self.req else {},
                    'headers': self.headers or {}
                })

            functionCallRes = await function_call({
                'configuration': self.customConfig,
                'apikey': self.apikey,
                'bridge': self.bridge,
                'tools_call' : _.get(modelResponse, self.modelOutputConfig.get('tools'))[0],
                'outputConfig': self.modelOutputConfig,
                'l': 0,
                'rtlLayer': self.rtlLayer,
                'body': self.req.json if self.req else {},
                'playground': self.playground,
                'tools': {}
            })
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

                asyncio.create_task(ResponseSender.sendResponse(
                    rtl_layer = self.rtlLayer,
                    webhook= self.webhook,
                    data=  {'error': functionCallRes.get('error'), 'success': False},
                    req_body=  self.req.json if self.req else {},
                    headers= self.headers or {}
                ))
                if self.rtlLayer or self.webhook:
                    return

                return {'success': False, 'error': functionCallRes.get('error')}
            self.total_tokens = _.get(modelResponse, self.modelOutputConfig['usage'][0]['total_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['total_tokens'])
            self.prompt_tokens = _.get(modelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'])
            self.completion_tokens = _.get(modelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(funcModelResponse, self.modelOutputConfig['usage'][0]['completion_tokens'])
            
            _.set_(modelResponse, self.modelOutputConfig['message'], _.get(funcModelResponse, self.modelOutputConfig['message']))
            _.set_(modelResponse, self.modelOutputConfig['tools'], _.get(funcModelResponse, self.modelOutputConfig['tools']))
            _.set_(modelResponse, self.modelOutputConfig['usage'][0]['total_tokens'], self.total_tokens)
            _.set_(modelResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'], self.prompt_tokens)
            _.set_(modelResponse, self.modelOutputConfig['usage'][0]['completion_tokens'], self.completion_tokens)


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
