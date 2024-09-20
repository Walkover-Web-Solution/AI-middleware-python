import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name

class UnifiedOpenAICase(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        tools_call_data = []
        conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation')).get('messages', [])
        self.customConfig["messages"] = [ {"role": "system", "content": self.configuration['prompt']}] + conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
        self.customConfig =self.service_formatter(self.customConfig, service_name['openai'])
        if 'tools' not in self.customConfig and 'parallel_tool_calls' in self.customConfig:
            del self.customConfig['parallel_tool_calls']
        openAIResponse = await self.chats(self.customConfig, self.apikey, service_name['openai'])
        modelResponse = openAIResponse.get("modelResponse", {})
        if not openAIResponse.get('success'):
            if not self.playground:
                await self.handle_failure(openAIResponse)
            raise ValueError(openAIResponse.get('error'))
        if len(modelResponse.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0:
            tools_call_data.extend(modelResponse.get('choices', [])[0].get('message', {}).get("tool_calls", []))
            functionCallRes = await self.function_call(self.customConfig, service_name['openai'], openAIResponse)
            if not functionCallRes.get('success'):
                await self.handle_failure(functionCallRes)
                raise ValueError(functionCallRes.get('error'))
            self.update_model_response(modelResponse, functionCallRes)
            tools = functionCallRes.get("tools", {}) 

        usage = self.calculate_usage(modelResponse)
        if not self.playground:
            historyParams = self.prepare_history_params(modelResponse, tools)
            historyParams["tools_call_data"] = tools_call_data
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage}