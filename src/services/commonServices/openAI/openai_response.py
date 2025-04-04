import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name

class OpenaiResponse(BaseService):
    async def execute(self):
        historyParams, usage, tools = {}, {}, {}
        conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
        
        user = [{"role": "user", "content": self.user}] if self.user else []
        developer = [{"role": "developer", "content": self.configuration['prompt']}] if not self.reasoning_model else []
        
        if self.image_data:
            self.customConfig["input"] = developer + conversation
            if self.user:
                user = [{"type": "text", "text": self.user}]
                if isinstance(self.image_data, list):
                    user.extend({"type": "image_url", "image_url": {"url": image_url}} for image_url in self.image_data)
                self.customConfig["messages"].append({'role': 'user', 'content': user})
        else:
            self.customConfig["input"] = developer + conversation + user
        
        self.customConfig = self.service_formatter(self.customConfig, service_name['openai'])
        
        if 'tools' not in self.customConfig and 'parallel_tool_calls' in self.customConfig:
            del self.customConfig['parallel_tool_calls']
        
        openAIResponse = await self.chats(self.customConfig, self.apikey, service_name['openai_response'])
        modelResponse = openAIResponse.get("modelResponse", {})
        
        if not openAIResponse.get('success'):
            if not self.playground:
                await self.handle_failure(openAIResponse)
            raise ValueError(openAIResponse.get('error'))
        
        # if modelResponse.get('choices', [])[0].get('message', {}).get("tool_calls"):
        #     functionCallRes = await self.function_call(self.customConfig, service_name['openai'], openAIResponse, 0, {})
        #     if not functionCallRes.get('success'):
        #         await self.handle_failure(functionCallRes)
        #         raise ValueError(functionCallRes.get('error'))
        #     self.update_model_response(modelResponse, functionCallRes)
        #     tools = functionCallRes.get("tools", {})
        
        if not self.playground:
            usage = self.token_calculator.calculate_usage(modelResponse)
            historyParams = self.prepare_history_params(modelResponse, tools)
        
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage }
    