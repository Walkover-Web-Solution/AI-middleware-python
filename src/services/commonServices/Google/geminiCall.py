import pydash as _
import json
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.services.utils.ai_middleware_format import Response_formatter
from google.genai import types
from .gemini_utils import convert_to_gemini_format

class GeminiHandler(BaseService):
    async def execute(self):
        historyParams = {}
        tools = {}
        functionCallRes = {}
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
                historyParams = self.prepare_history_params(response, model_response, tools, None)
                historyParams['message'] = "image generated successfully"
                historyParams['type'] = 'assistant'
        elif self.file_data or self.youtube_url:
            self.customConfig['prompt'] = self.user
            if self.youtube_url:
                self.customConfig['youtube_url'] = self.youtube_url
            gemini_response = await self.video(self.customConfig, self.apikey, service_name['gemini'])
            model_response = gemini_response.get("modelResponse", {})
            if not gemini_response.get('success'):
                if not self.playground:
                    await self.handle_failure(gemini_response)
                raise ValueError(gemini_response.get('error'))
            self.type = 'video'
            response = await Response_formatter(model_response, service_name['gemini'], tools, self.type, self.file_data)
            if not self.playground:
                historyParams = self.prepare_history_params(response, model_response, tools, None)
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
                
            formatted_config = self.service_formatter(self.customConfig, service_name['gemini'])
            if 'tools' not in formatted_config and 'parallel_tool_calls' in formatted_config:
                del formatted_config['parallel_tool_calls']
            
            formatted_config_for_tools = formatted_config 

            # Convert to Gemini SDK format
            self.customConfig = convert_to_gemini_format(formatted_config)
            
            gemini_response = await self.chats(self.customConfig, self.apikey, service_name['gemini'])
            model_response = gemini_response.get('modelResponse', {})
            if not gemini_response.get('success'):
                if not self.playground:
                    await self.handle_failure(gemini_response)
                raise ValueError(gemini_response.get('error'))
            

            # Handle tool calls
            candidates = model_response.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                has_function_calls = any(isinstance(part, dict) and part.get('function_call') is not None for part in parts)
                if has_function_calls:
                    tool_calls = []

                    for idx, part in enumerate(parts):
                        if isinstance(part, dict) and part.get('function_call') is not None:
                            fc = part['function_call'] or {}
                            tool_calls.append({
                                "id": f"call_{idx}_{fc.get('name', 'unknown')}",
                                "type": "function",
                                "function": {
                                    "name": fc.get('name'),
                                    'arguments': json.dumps(fc.get('args', {}))
                                }
                            })
            
                    if 'choices' not in model_response:
                        model_response['choices'] = [{}]
                    if 'message' not in model_response['choices'][0]:
                        model_response['choices'][0]['message'] = {}
                    model_response['choices'][0]['message']['tool_calls'] = tool_calls

                    functionCallRes = await self.function_call(formatted_config_for_tools, service_name['gemini'], gemini_response)
                    if not functionCallRes.get('success'):
                        await self.handle_failure(functionCallRes)
                        raise ValueError(functionCallRes.get('error'))
            if functionCallRes:
                tools = functionCallRes.get('tools', {})
                # Use the final response from function_call, not the initial one
                model_response = functionCallRes.get('modelResponse', model_response)
            
            response = await Response_formatter(model_response, service_name['gemini'], tools, self.type, self.image_data)
            if not self.playground:
                transfer_config = functionCallRes.get('transfer_agent_config') if functionCallRes else None
                historyParams = self.prepare_history_params(response, model_response, tools, transfer_config)
        
        result = {'success': True, 'modelResponse': model_response, 'historyParams': historyParams, 'response': response}
        if functionCallRes.get('transfer_agent_config'):
            result['transfer_agent_config'] = functionCallRes['transfer_agent_config']
        return result

    async def chats(self, configuration, apikey, service, count=0):
        """Override chats to convert OpenAI format to Gemini SDK format"""
        # Convert OpenAI format to Gemini format before API call
        if 'messages' in configuration:
            configuration = convert_to_gemini_format(configuration)
        
        # Call parent chats method with converted config
        return await super().chats(configuration, apikey, service, count)