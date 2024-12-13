import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name

class UnifiedOpenAICase(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        if self.type == 'image':
            self.customConfig['prompt'] = self.user
            openAIResponse = await self.image(self.customConfig, self.apikey, service_name['openai'])
            modelResponse = openAIResponse.get("modelResponse", {})
            if not openAIResponse.get('success'):
                if not self.playground:
                    await self.handle_failure(openAIResponse)
                raise ValueError(openAIResponse.get('error'))
        else:
            conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
            if self.reasoning_model:
                prompt = [{"role": "user", "content": f"system Prompt: {self.configuration.get('prompt')}"}]
                self.customConfig["messages"] = prompt + conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
            else:
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
                functionCallRes = await self.function_call(self.customConfig, service_name['openai'], openAIResponse, 0, {})
                if not functionCallRes.get('success'):
                    await self.handle_failure(functionCallRes)
                    raise ValueError(functionCallRes.get('error'))
                self.update_model_response(modelResponse, functionCallRes)
                tools = functionCallRes.get("tools", {})
            usage = self.calculate_usage(modelResponse)
            if not self.playground:
                historyParams = self.prepare_history_params(modelResponse, tools)
                historyParams['message'] = "image generated successfully"
                historyParams['type'] = 'assistant'
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage }
    