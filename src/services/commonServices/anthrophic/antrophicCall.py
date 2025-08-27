import pydash as _
from ..baseService.baseService import BaseService
from src.configs.constant import service_name
from ..createConversations import ConversationService
from ....services.utils.apiservice import  fetch_images_b64
from src.services.utils.ai_middleware_format import Response_formatter


class Antrophic(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = []
        images_input = []
        conversation = (await ConversationService.createAnthropicConversation(self.configuration.get('conversation'), self.memory, self.files)).get('messages', [])        
        self.customConfig['system'] = self.configuration.get('prompt')
        if self.image_data:
            images_data = await fetch_images_b64(self.image_data)
            images_input = [{'type': 'image', 'source': {'type': 'base64', 'media_type': image_media_type, 'data': image_data}} for image_data, image_media_type in images_data]
        elif self.files and len(self.files) > 0:
            # Handle files (documents) when no images
            file_content = [{'type': 'document', 'source': {'type': 'url', 'url': file_url}} for file_url in self.files]
            content = file_content + [{"type": "text", "text": self.user}] if self.user else file_content
            self.customConfig["messages"] = conversation + [{"role": "user", "content": content}]
        
        # Original image handling logic (only runs if no files or images_input is populated)
        if not (self.files and len(self.files) > 0):
            self.customConfig["messages"] = conversation + [{"role": "user", "content": (images_input + [{"type": "text", "text": self.user}] if self.user else images_input)}] if images_input or self.user else conversation
        self.customConfig['tools'] = self.tool_call if self.tool_call and len(self.tool_call) != 0 else []
        self.customConfig = self.service_formatter(self.customConfig, service_name['anthropic'])
        antrophic_response = await self.chats(self.customConfig, self.apikey, service_name['anthropic'])
        modelResponse = antrophic_response.get("modelResponse", {})
        
        if not antrophic_response.get('success'):
            if not self.playground:
                await self.handle_failure(antrophic_response)
            raise ValueError(antrophic_response.get('error'))
        functionCallRes = await self.function_call(self.customConfig, service_name['anthropic'], antrophic_response, 0, {})
        if not functionCallRes.get('success'):
            await self.handle_failure(functionCallRes)
            raise ValueError(functionCallRes.get('error'))
        
        self.update_model_response(modelResponse, functionCallRes)
        tools = functionCallRes.get("tools", {})
        response = await Response_formatter(modelResponse, service_name['anthropic'], tools, self.type, self.image_data)
        if not self.playground:
            historyParams = self.prepare_history_params(response, modelResponse, tools)
        return {'success': True, 'modelResponse': modelResponse, 'historyParams': historyParams, 'response': response }