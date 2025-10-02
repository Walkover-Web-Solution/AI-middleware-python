import asyncio
import json
from config import Config
from aio_pika.abc import AbstractIncomingMessage
from src.services.utils.logger import logger
from src.db_services.metrics_service import create
from src.services.utils.ai_middleware_format import validateResponse
from src.services.commonServices.bridge_avg_response_time import get_bridge_avg_response_time
from src.services.utils.gpt_memory import handle_gpt_memory
from src.services.commonServices.suggestion import chatbot_suggestions
from src.services.commonServices.baseService.utils import total_token_calculation, save_files_to_redis  
from src.controllers.conversationController import save_sub_thread_id_and_name
from src.services.commonServices.queueService.baseQueue import BaseQueue


class Queue2(BaseQueue):
    _instance = None

    def __new__(cls):
        """Ensure a singleton instance for the log queue consumer."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        """Initialise the log queue with environment-specific naming."""
        queue_name = Config.LOG_QUEUE_NAME or f"AI-MIDDLEARE-DATA-QUEUE-{Config.ENVIROMENT}"
        super().__init__(queue_name)
        print("Queue2 Service Initialized")

    async def process_messages(self, messages):
        """Implement your batch processing logic here."""
        await save_sub_thread_id_and_name(**messages['save_sub_thread_id_and_name'])
        
        # If message type is 'image', only run save_sub_thread_id_and_name
        if messages.get('type') == 'image':
            return
        # await create(**messages['metrics_service'])
        await validateResponse(**messages['validateResponse'])
        await total_token_calculation(**messages['total_token_calculation'])
        await get_bridge_avg_response_time(**messages['get_bridge_avg_response_time'])
        if messages['check_handle_gpt_memory']['gpt_memory']:
            await handle_gpt_memory(**messages['handle_gpt_memory'])
        if messages['check_chatbot_suggestions']['bridgeType']:
            await chatbot_suggestions(**messages['chatbot_suggestions'])
        await save_files_to_redis(**messages['save_files_to_redis'])


    async def consume_messages(self):
        """Continuously consume log messages and pass them to the handler."""
        try:
            if await self.connect():
                await self.channel.set_qos(prefetch_count=int(self.prefetch_count))
                primary_queue = await self.channel.declare_queue(self.queue_name, durable=True)

                print(f"Started consuming from queue {self.queue_name}")
                logger.info(f"Started consuming from queue {self.queue_name}")
                
                # Using the message handler wrapper from BaseQueue with direct reference to process_messages
                await primary_queue.consume(
                    lambda message: self._message_handler_wrapper(message, self.process_messages)
                )
                
                while True:
                    await asyncio.sleep(1)  # Keeps the consumer running indefinitely, can do something work too if needed
        except Exception as e:
            logger.error(f"Error while consuming messages: {e}")

sub_queue_obj = Queue2()
