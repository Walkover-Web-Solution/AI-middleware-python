import pydash as _
from ..baseService.baseService import BaseService
from .antrophicChats import chats
from src.configs.constant import service_name
from ..createConversations import ConversationService

class Antrophic(BaseService):
    async def antrophic_handler(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = [] # create conversation according to claude models
        conversation = ConversationService.createAnthropicConversation(self.configuration.get('conversation')).get('messages', [])        
        self.customConfig['system'] = self.configuration.get('prompt')
        self.customConfig["messages"] =conversation + [{"role": "user", "content":[{ "type": "text","text": self.user }]  }]
        self.customConfig['tools'] = self.tool_call
        self.customConfig =self.service_formatter(self.customConfig, service_name['anthropic'])
        antrophic_response = await chats(self.customConfig, self.apikey)
        modelResponse = antrophic_response.get("modelResponse", {})
        if not antrophic_response.get('success'):
            if not self.playground:
                await self.handle_failure(antrophic_response)
            return {'success': False, 'error': antrophic_response.get('error')}
        
        functionCallRes = await self.function_call(self.customConfig,{
                'apikey': self.apikey,
                'response_format' : self.response_format,
                'playground': self.playground,
            },service_name['anthropic'], antrophic_response)
        if not functionCallRes.get('success'):
            await self.handle_failure(functionCallRes)
            return {'success': False, 'error': functionCallRes.get('error')}
        
        self.update_model_response(modelResponse, functionCallRes)
        tools = functionCallRes.get("tools", {})

        usage = self.calculate_usage(modelResponse)
        if not self.playground:
            historyParams = self.prepare_history_params(modelResponse, tools)
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage}