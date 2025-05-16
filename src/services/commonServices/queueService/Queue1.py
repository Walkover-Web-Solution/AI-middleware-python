# queue1.py

import asyncio
from config import Config
from src.services.utils.logger import logger
from src.services.commonServices.common import chat
#from base_queue import BaseQueue
from src.services.commonServices.queueService.baseQueue import BaseQueue

class Queue(BaseQueue):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()  # Ensure init is called only once
        return cls._instance

    def __init__(self):
        queue_name = Config.QUEUE_NAME or "AI-MIDDLEARE-DEFAULT"
        super().__init__(queue_name)
        print("Queue Service Initialized")

    async def process_messages(self, messages):
        """Main processing logic for Queue"""
        loop = asyncio.get_event_loop()
        await chat(messages)

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

queue_obj = Queue()