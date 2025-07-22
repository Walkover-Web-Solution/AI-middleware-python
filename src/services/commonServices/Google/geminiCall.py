import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.services.utils.ai_middleware_format import Response_formatter

class GeminiHandler(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        if self.type == 'image':
            self.customConfig['prompt'] = self.user
            gemini_response = await self.image(self.customConfig, self.apikey, service_name['gemini'])
            model_response = gemini_response.get("modelResponse", {})
            if not gemini_response.get('success'):
                if not self.playground:
                    await self.handle_failure(gemini_response)
                raise ValueError(gemini_response.get('error'))
            response = await Response_formatter(model_response, service_name['gemini'], tools, self.type, self.image_data)
            if not self.playground:
                historyParams = self.prepare_history_params(response, model_response, tools)
                historyParams['message'] = "image generated successfully"
                historyParams['type'] = 'assistant'
        else:
            conversation = ConversationService.createGeminiConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
            if self.reasoning_model:
                self.customConfig["messages"] =  conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
            else:
                if not self.image_data:
                    self.customConfig["messages"] = [ {"role": "developer", "content": self.configuration['prompt']}] + conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
                else:
                    self.customConfig["messages"] = [{"role": "developer", "content": self.configuration['prompt']}] + conversation
                    user_content = []
                    if self.user:
                        user_content = [{"type": "text", "text": self.user}]
                    if isinstance(self.image_data, list):
                        for image_url in self.image_data:
                            user_content.append({"type": "image_url", "image_url": {"url": image_url}})
                    self.customConfig["messages"].append({'role': 'user', 'content': user_content})
                self.customConfig =self.service_formatter(self.customConfig, service_name['gemini'])
                if 'tools' not in self.customConfig and 'parallel_tool_calls' in self.customConfig:
                    del self.customConfig['parallel_tool_calls']
            gemini_response = await self.chats(self.customConfig, self.apikey, service_name['gemini'])
            model_response = gemini_response.get("modelResponse", {})
            if not gemini_response.get('success'):
                if not self.playground:
                    await self.handle_failure(gemini_response)
                raise ValueError(gemini_response.get('error'))
            if len(model_response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0:
                functionCallRes = await self.function_call(self.customConfig, service_name['gemini'], gemini_response, 0, {})
                if not functionCallRes.get('success'):
                    await self.handle_failure(functionCallRes)
                    raise ValueError(functionCallRes.get('error'))
                self.update_model_response(model_response, functionCallRes)
                tools = functionCallRes.get("tools", {})
            response = await Response_formatter(model_response, service_name['gemini'], tools, self.type, self.image_data)
            if not self.playground:
                usage = self.token_calculator.calculate_usage(model_response)
                historyParams = self.prepare_history_params(response, model_response, tools)
        return {'success': True, 'modelResponse': model_response, 'historyParams': historyParams, 'usage': usage, 'response': response }
    