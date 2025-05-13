# queue2.py

import asyncio
from config import Config
from src.services.utils.logger import logger
from src.db_services.ConfigurationServices import save_sub_thread_id
from src.db_services.metrics_service import create
from src.services.utils.ai_middleware_format import validateResponse
from src.services.commonServices.baseService.utils import total_token_calculation
from src.services.commonServices.bridge_avg_response_time import get_bridge_avg_response_time
from src.services.utils.gpt_memory import handle_gpt_memory
from src.services.commonServices.suggestion import chatbot_suggestions
#from base_queue import BaseQueue
from src.services.commonServices.queueService.baseQueue import BaseQueue

class Queue2(BaseQueue):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        queue_name = Config.LOG_QUEUE_NAME or f"AI-MIDDLEARE-DATA-QUEUE-{Config.ENVIROMENT}"
        super().__init__(queue_name)
        print("Queue2 Service Initialized")

    async def process_messages(self, messages):
        """Main processing logic for Queue2"""
        await save_sub_thread_id(**messages['save_sub_thread_id'])
        await create(**messages['metrics_service'])
        await validateResponse(**messages['validateResponse'])
        await total_token_calculation(**messages['total_token_calculation'])
        await get_bridge_avg_response_time(**messages['get_bridge_avg_response_time'])

        if messages['check_chatbot_suggestions']['bridgeType']:
            await chatbot_suggestions(**messages['chatbot_suggestions'])

        if messages['check_handle_gpt_memory']['gpt_memory'] and messages['check_handle_gpt_memory']['type'] == 'chat':
            await handle_gpt_memory(**messages['handle_gpt_memory'])

    async def consume_messages(self):
        try:
            if await self.connect():
                await self.channel.set_qos(prefetch_count=self.prefetch_count)
                queue = await self.channel.declare_queue(self.queue_name, durable=True)
                
                async def handler(message):
                    await self._message_handler_wrapper(message, self.process_messages)

                await queue.consume(handler)
                logger.info(f"Started consuming from {self.queue_name}")
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Consumer error: {e}")

sub_queue_obj = Queue2()