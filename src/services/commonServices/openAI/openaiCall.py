import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name

class UnifiedOpenAICase(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation')).get('messages', [])
        self.customConfig["messages"] = [ {"role": "system", "content": self.configuration['prompt']}] + conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
        self.customConfig =self.service_formatter(self.customConfig, service_name['openai'])
        openAIResponse = await self.chats(self.customConfig, self.apikey, service_name['openai'])
        modelResponse = openAIResponse.get("modelResponse", {})
        if not openAIResponse.get('success'):
            if not self.playground:
                await self.handle_failure(openAIResponse)
            return {'success': False, 'error': openAIResponse.get('error')}
        if _.get(modelResponse, self.modelOutputConfig.get('tools')):
            functionCallRes = await self.function_call(self.customConfig, service_name['openai'], openAIResponse)
            if not functionCallRes.get('success'):
                await self.handle_failure(functionCallRes)
                return {'success': False, 'error': functionCallRes.get('error')}
            self.update_model_response(modelResponse, functionCallRes)
            tools = functionCallRes.get("tools", {}) 

        usage = self.calculate_usage(modelResponse)
        if not self.playground:
            historyParams = self.prepare_history_params(modelResponse, tools)
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage}