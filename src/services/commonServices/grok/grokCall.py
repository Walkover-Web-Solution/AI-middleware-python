from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
from src.services.utils.ai_middleware_format import Response_formatter


class Grok(BaseService):
    async def execute(self):
        historyParams = {}
        tools = {}
        functionCallRes = {}

        conversation = ConversationService.createGrokConversation(
            self.configuration.get('conversation'),
            self.memory
        ).get('messages', [])

        self.customConfig["messages"] = (
            [{"role": "system", "content": self.configuration['prompt']}]
            + conversation
            + ([{"role": "user", "content": self.user}] if self.user else [])
        )

        self.customConfig = self.service_formatter(self.customConfig, service_name['grok'])

        grok_response = await self.chats(self.customConfig, self.apikey, service_name['grok'])
        model_response = grok_response.get("modelResponse", {})

        if not grok_response.get('success'):
            if not self.playground:
                await self.handle_failure(grok_response)
            raise ValueError(grok_response.get('error'))

        if len(model_response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0:
            functionCallRes = await self.function_call(
                self.customConfig,
                service_name['grok'],
                grok_response,
                0,
                {}
            )

            if not functionCallRes.get('success'):
                await self.handle_failure(functionCallRes)
                raise ValueError(functionCallRes.get('error'))

            self.update_model_response(model_response, functionCallRes)
            tools = functionCallRes.get("tools", {})

        response = await Response_formatter(
            model_response,
            service_name['grok'],
            tools,
            self.type,
            self.image_data
        )

        if not self.playground:
            transfer_config = functionCallRes.get('transfer_agent_config') if functionCallRes else None
            historyParams = self.prepare_history_params(response, model_response, tools, transfer_config)

        result = {
            'success': True,
            'modelResponse': model_response,
            'historyParams': historyParams,
            'response': response
        }

        if functionCallRes.get('transfer_agent_config'):
            result['transfer_agent_config'] = functionCallRes['transfer_agent_config']

        return result
