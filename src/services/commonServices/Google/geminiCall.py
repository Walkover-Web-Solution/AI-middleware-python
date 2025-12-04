import pydash as _
import aiohttp
import base64
import re
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.services.utils.ai_middleware_format import Response_formatter
from globals import logger

class GeminiHandler(BaseService):
    async def _convert_url_to_base64(self, url):
        """
        Convert HTTP URL to base64 data URL for Gemini compatibility
        """
        try:
            import ssl
            # Create SSL context that doesn't verify certificates for internal resources
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('content-type', 'application/octet-stream')
                        
                        # Encode to base64
                        base64_content = base64.b64encode(content).decode('utf-8')
                        
                        # Return as data URL
                        return f"data:{content_type};base64,{base64_content}"
                    else:
                        logger.warning(f"Failed to fetch URL {url}: HTTP {response.status}")
                        return url
        except Exception as e:
            logger.error(f"Error converting URL to base64: {e}")
            return url
    
    def _is_http_url(self, url):
        """
        Check if the URL is an HTTP/HTTPS URL
        """
        return isinstance(url, str) and (url.startswith('http://') or url.startswith('https://'))
    
    def _is_image_url(self, url):
        """
        Check if URL points to an image based on file extension
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico', '.heic', '.heif']
        return any(url.lower().endswith(ext) for ext in image_extensions)

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
            conversation_result = await ConversationService.createGeminiConversation(self.configuration.get('conversation'), self.memory, self.files)
            conversation = conversation_result.get('messages', [])
            if self.reasoning_model:
                self.customConfig["messages"] =  conversation + ([{"role": "user", "content": self.user}] if self.user else []) 
            else:
                developer = [{"role": "developer", "content": self.configuration['prompt']}] if not self.reasoning_model else []
                
                if self.image_data and isinstance(self.image_data, list):
                    self.customConfig["messages"] = developer + conversation
                    user_content = []
                    if self.user:
                        user_content = [{"type": "text", "text": self.user}]
                    
                    # Process image URLs - pass directly to Gemini (will fallback if HTTP URLs fail)
                    for image_url in self.image_data:
                        user_content.append({"type": "image_url", "image_url": {"url": image_url}})
                    
                    self.customConfig["messages"].append({'role': 'user', 'content': user_content})
                elif self.files and len(self.files) > 0:
                    self.customConfig["messages"] = developer + conversation
                    user_content = []
                    if self.user:
                        user_content = [{"type": "text", "text": self.user}]
                    
                    # Process files - pass directly to Gemini (will fallback if HTTP URLs fail)
                    for file_url in self.files:
                        if self._is_image_url(file_url) or file_url.startswith('data:image/'):
                            # Handle as image
                            user_content.append({"type": "image_url", "image_url": {"url": file_url}})
                        else:
                            # Handle as file content - Gemini will reject this and fallback to other services
                            user_content.append({"type": "input_file", "file_url": file_url})
                    
                    self.customConfig["messages"].append({'role': 'user', 'content': user_content})
                else:
                    self.customConfig["messages"] = developer + conversation + ([{"role": "user", "content": self.user}] if self.user else [])
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
                transfer_config = functionCallRes.get('transfer_agent_config') if functionCallRes else None
                historyParams = self.prepare_history_params(response, model_response, tools, transfer_config)
        # Add transfer_agent_config to return if transfer was detected
        result = {'success': True, 'modelResponse': model_response, 'historyParams': historyParams, 'response': response}
        if functionCallRes.get('transfer_agent_config'):
            result['transfer_agent_config'] = functionCallRes['transfer_agent_config']
        return result
    