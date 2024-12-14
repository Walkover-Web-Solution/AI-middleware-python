import pydash as _
import json
import traceback
from ..baseService.baseService import BaseService
from src.configs.constant import service_name
from ..createConversations import ConversationService
from ..Google.geminiModelRun import gemini_runmodel
from ....db_services import metrics_service

class GeminiHandler(BaseService):
    async def execute(self):
        historyParams = {}
        usage = {}
        tools = {}
        conversation = ConversationService.createGeminiConversation(self.configuration.get('conversation'), self.memory).get('messages', [])
        
        self.customConfig['system'] = self.configuration.get('prompt')
        self.customConfig['user'] = self.user
        self.customConfig["messages"] = conversation + [{"role": "user", "parts": self.user}] if self.user else conversation
        self.customConfig['tools'] = self.tool_call if self.tool_call else []
        self.customConfig = self.service_formatter(self.customConfig, service_name['gemini'])
        
        gemini_response = await self.chats(self.customConfig, self.apikey, service_name['gemini'])
        modelResponse = gemini_response.get("modelResponse", {})
        
        if not gemini_response.get('success'):
            if not self.playground:
                await self.handle_failure(gemini_response)
            raise ValueError(gemini_response.get('error'))
        
        # Handle function calls
        # functionCallRes = await self.function_call(self.customConfig, service_name['gemini'], gemini_response, 0, {})
        # if not functionCallRes.get('success'):
        #     if not self.playground:
        #         await self.handle_failure(functionCallRes)
        #     raise ValueError(functionCallRes.get('error'))
        
        # Update response and tools
        # self.update_model_response(modelResponse, functionCallRes)
        # tools = functionCallRes.get("tools", {})
        
        # Calculate usage
        usage = self.calculate_usage(modelResponse)
        
        if not self.playground:
            historyParams = self.prepare_history_params(modelResponse, tools)
        
        return {'success': True,'modelResponse': modelResponse,'historyParams': historyParams,'usage': usage}
