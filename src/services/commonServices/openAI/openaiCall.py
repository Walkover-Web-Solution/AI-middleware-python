import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.services.utils.ai_middleware_format import Response_formatter

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
            response = await Response_formatter(modelResponse, service_name['openai'], tools, self.type, self.image_data)
            if not self.playground:
                historyParams = self.prepare_history_params(response, modelResponse, tools)
                historyParams['message'] = "image generated successfully"
                historyParams['type'] = 'assistant'
        else:
            conversation = ConversationService.createOpenAiConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
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
                # Check for transfer action_type before executing function calls
                from src.services.utils.transfer_handler import should_skip_function_call
                
                has_transfer, transfer_agent_config = should_skip_function_call(modelResponse, self.customConfig)
                
                # Skip function call execution if transfer found, otherwise execute normally
                if not has_transfer:
                    functionCallRes = await self.function_call(self.customConfig, service_name['openai'], openAIResponse, 0, {})
                    if not functionCallRes.get('success'):
                        await self.handle_failure(functionCallRes)
                        raise ValueError(functionCallRes.get('error'))
                    self.update_model_response(modelResponse, functionCallRes)
                    tools = functionCallRes.get("tools", {})
                else:
                    tools = {}
            response = await Response_formatter(modelResponse, service_name['openai'], tools, self.type, self.image_data)
            if not self.playground:
                usage = self.token_calculator.calculate_usage(modelResponse)
                historyParams = self.prepare_history_params(response, modelResponse, tools)
        # Add transfer_agent_config to return if transfer was detected
        result = {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'usage': usage, 'response': response}
        if 'transfer_agent_config' in locals() and transfer_agent_config:
            result['transfer_agent_config'] = transfer_agent_config
        return result
    