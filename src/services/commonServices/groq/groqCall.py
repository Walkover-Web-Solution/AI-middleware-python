import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.services.utils.ai_middleware_format import Response_formatter

class Groq(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = ConversationService.createGroqConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
        self.customConfig["messages"] = [{"role": "system", "content": self.configuration['prompt']}] + conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
        self.customConfig =self.service_formatter(self.customConfig, service_name['groq'])
        
        groq_response = await self.chats(self.customConfig, self.apikey, 'groq')
        model_response = groq_response.get("modelResponse", {})
        
        if not groq_response.get('success'):
            if not self.playground:
                await self.handle_failure(groq_response)
            raise ValueError(groq_response.get('error'))
        
        if len(model_response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0:
            # Check for transfer action_type before executing function calls
            from src.services.utils.transfer_handler import should_skip_function_call
            
            has_transfer, transfer_agent_config = should_skip_function_call(model_response, self.customConfig)
            
            # Skip function call execution if transfer found, otherwise execute normally
            if not has_transfer:
                functionCallRes = await self.function_call(self.customConfig, service_name['groq'], groq_response, 0, {})
                
                if not functionCallRes.get('success'):
                    await self.handle_failure(functionCallRes)
                    raise ValueError(functionCallRes.get('error'))
                
                self.update_model_response(model_response, functionCallRes)
                tools = functionCallRes.get("tools", {})
            else:
                tools = {} 
            
        response = await Response_formatter(model_response, service_name['groq'], tools, self.type, self.image_data)
        if not self.playground:
            usage = self.token_calculator.calculate_usage(model_response)
            historyParams = self.prepare_history_params(response, model_response, tools)
        
        # Add transfer_agent_config to return if transfer was detected
        result = {'success': True, 'modelResponse': model_response, 'historyParams': historyParams, 'usage': usage, 'response': response}
        if 'transfer_agent_config' in locals() and transfer_agent_config:
            result['transfer_agent_config'] = transfer_agent_config
        return result