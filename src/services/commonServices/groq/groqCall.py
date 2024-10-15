import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name

class Groq(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation')).get('messages', [])
        self.customConfig["messages"] = [{"role": "system", "content": self.configuration['prompt']}] + conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
        self.customConfig =self.service_formatter(self.customConfig, service_name['groq'])
        
        groq_response = await self.chats(self.customConfig, self.apikey, 'groq')
        model_response = groq_response.get("modelResponse", {})
        
        if not groq_response.get('success'):
            if not self.playground:
                await self.handle_failure(groq_response)
            raise ValueError(groq_response.get('error'))
        
        if len(model_response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0:
            functionCallRes = await self.function_call(self.customConfig, service_name['groq'], groq_response, 0, {})
            
            if not functionCallRes.get('success'):
                await self.handle_failure(functionCallRes)
                raise ValueError(functionCallRes.get('error'))
            
            self.update_model_response(model_response, functionCallRes)
            tools = functionCallRes.get("tools", {}) 
            
        usage = self.calculate_usage(model_response)
        
        if not self.playground:
            historyParams = self.prepare_history_params(model_response, tools)
        
        return {'success': True, 'modelResponse': model_response, 'historyParams': historyParams, 'usage': usage }