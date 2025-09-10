import asyncio
import json
from config import Config
from src.services.commonServices.common import chat, image, orchestrator_chat
from aio_pika.abc import AbstractIncomingMessage
from src.services.utils.logger import logger
from src.services.utils.common_utils import process_background_tasks
from src.services.commonServices.queueService.baseQueue import BaseQueue


class Queue(BaseQueue):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()  # Ensure init is called only once
        return cls._instance

    def __init__(self):
        queue_name = Config.QUEUE_NAME or f"AI-MIDDLEARE-DEFAULT-{Config.ENVIROMENT}"
        super().__init__(queue_name)
        print("Queue Service Initialized")

    async def process_messages(self, messages):
        """Implement your batch processing logic here."""
        # Check if this is an orchestrator request
        body = messages.get("body", {})
        
        # Check for orchestrator indicators in the request
        has_orchestrator_id = body.get('master_agent_id') or body.get('orchestrator_id')
        has_agent_configurations = body.get('agent_configurations') or body.get('master_agent_config')
        
        # If it looks like an orchestrator request, handle it accordingly
        if has_orchestrator_id and has_agent_configurations:
            # Call orchestrator_chat same as chat - both expect messages format
            await orchestrator_chat(messages)
            return
        
        # Handle regular chat/image requests
        type = body.get('configuration', {}).get('type')
        if type == 'image':
            await image(messages)
            return
        await chat(messages)
        # return result

    async def consume_messages(self):
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

queue_obj = Queue()