import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.configs.model_configuration import model_config_document

class OpenaiResponse(BaseService):
    async def execute(self):
        historyParams, usage, tools = {}, {}, {}
        conversation = ConversationService.createOpenAiResponseConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
        
        developer = [{"role": "developer", "content": self.configuration['prompt']}] if not self.reasoning_model else []
        
        if self.image_data and isinstance(self.image_data, list):
            self.customConfig["input"] = developer + conversation
            image_content = [{"type": "input_image", "image_url": url} for url in self.image_data]
            content = [{"type": "input_text", "text": self.user}] + image_content if self.user else image_content
            self.customConfig["input"].append({'role': 'user', 'content': content})
        else:
            user = [{"role": "user", "content": self.user}] if self.user else []
            self.customConfig["input"] = developer + conversation + user
        
        self.customConfig = self.service_formatter(self.customConfig, service_name['openai_response'])
        
        if 'tools' not in self.customConfig and 'parallel_tool_calls' in self.customConfig:
            del self.customConfig['parallel_tool_calls']
        
        if len(self.built_in_tools) > 0:
            if 'web_search' in self.built_in_tools and 'tools' in model_config_document[self.service][self.model]['configuration']:
                if 'tools' not in self.customConfig:
                    self.customConfig['tools'] = []
                self.customConfig['tools'].append({"type": "web_search_preview"})

        openAIResponse = await self.chats(self.customConfig, self.apikey, service_name['openai_response'])
        modelResponse = openAIResponse.get("modelResponse", {})
        
        if not openAIResponse.get('success'):
            if not self.playground:
                await self.handle_failure(openAIResponse)
            raise ValueError(openAIResponse.get('error'))
        
        if modelResponse.get('output', [])[0].get('type') == 'function_call':
            functionCallRes = await self.function_call(self.customConfig, service_name['openai_response'], openAIResponse, 0, {})
            if not functionCallRes.get('success'):
                await self.handle_failure(functionCallRes)
                raise ValueError(functionCallRes.get('error'))
            self.update_model_response(modelResponse, functionCallRes)
            tools = functionCallRes.get("tools", {})
        
        if not self.playground:
            usage = self.token_calculator.calculate_usage(modelResponse)
            historyParams = self.prepare_history_params(modelResponse, tools)
        
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage }
    