import asyncio
from .gemini import run_chat
from ...commonServices.createConversations import ConversationService
from ....db_services import metrics_service
import time
import copy
import pydash as _

class GeminiHandler:
    def __init__(self, params):
        self.customConfig = params.get('customConfig')
        self.configuration = params.get('configuration')
        self.apikey = params.get('apikey')
        self.user = params.get('user')
        self.startTime = params.get('startTime')
        self.org_id = params.get('org_id')
        self.bridge_id = params.get('bridge_id')
        self.thread_id = params.get('thread_id')
        self.model = params.get('model')
        self.service = params.get('service')
        self.rtlayer = params.get('rtlayer')
        self.modelOutputConfig = params.get('modelOutputConfig')
        self.webhook = params.get('webhook')
        self.headers = params.get('headers')
        self.playground = params.get('playground')
        self.req = params.get('req')
        self.responseSender = ResponseSender()
        self.input = params.get('input')

    async def handle_gemini(self):
        usage = {}
        historyParams = {}

        geminiConfig = {
            'generationConfig': self.customConfig,
            'model': self.configuration.get('model'),
            'user_input': self.user,
        }
        if self.configuration.get('conversation'):
            geminiConfig["history"] = ConversationService.createGeminiConversation(self.configuration.get('conversation')).get('messages', [])

        geminiResponse = run_chat(geminiConfig, self.apikey, "chat")
        modelResponse = geminiResponse.get("modelResponse", {})
        if not geminiResponse.get('success'):
            usage = {
                'service': self.service,
                'model': self.model,
                'orgId': self.org_id,
                'latency': time.time() - self.startTime,
                'success': False,
                'error': geminiResponse.get('error'),
            }
            if not self.playground:
                metrics_service.create([usage], {
                    'thread_id': self.thread_id,
                    'user': self.user,
                    'message': "",
                    'org_id': self.org_id,
                    'bridge_id': self.bridge_id,
                    'model': self.configuration.get('model'),
                    'channel': 'chat',
                    'type': "error",
                    'actor': "user",
                })
                self.responseSender.send_response({
                    'rtlayer': self.rtlayer,
                    'webhook': self.webhook,
                    'data': {'success': False, 'error': geminiResponse.get('error')},
                    'reqBody': self.req.json if self.req else {},
                    'headers': self.headers or {},
                })
            raise ValueError(geminiResponse.get('error'))
        
        if not self.playground:
            usage["totalTokens"] = _.get(geminiResponse, self.modelOutputConfig['usage'][0]['total_tokens'])
            usage["inputTokens"] = _.get(geminiResponse, self.modelOutputConfig['usage'][0]['prompt_tokens'])
            usage["outputTokens"] = _.get(geminiResponse, self.modelOutputConfig['usage'][0]['output_tokens'])
            usage["expectedCost"] = self.modelOutputConfig['usage'][0]['total_cost']
            historyParams = {
                'thread_id': self.thread_id,
                'user': self.user,
                'message': modelResponse.get(self.modelOutputConfig['message']),
                'org_id': self.org_id,
                'bridge_id': self.bridge_id,
                'model': self.configuration.get('model'),
                'channel': 'chat',
                'type': "model",
                'actor': "user",
            }

        return {
            'success': True,
            'modelResponse': modelResponse,
            'usage': usage,
            'historyParams': historyParams,
        }
