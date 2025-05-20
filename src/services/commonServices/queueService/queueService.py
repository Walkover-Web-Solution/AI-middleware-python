import asyncio
import json
from config import Config
from src.services.commonServices.common import chat
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
        queue_name = Config.QUEUE_NAME or "AI-MIDDLEARE-DEFAULT"
        super().__init__(queue_name)
        print("Queue Service Initialized")

    async def process_messages(self, messages):
        """Implement your batch processing logic here."""
        loop = asyncio.get_event_loop()
        parsed_data, result, params, thread_info = await chat(messages)
        await process_background_tasks(parsed_data, result, params, thread_info)
        # return result

    async def consume_messages(self):
        try:
            if await self.connect():
                messages = []
                await self.channel.set_qos(prefetch_count=int(self.prefetch_count))
                primary_queue = await self.channel.declare_queue(self.queue_name, durable=True)

                async def message_handler(message: AbstractIncomingMessage):
                    async with message.process():
                        try:
                            print(f" [x] Received")
                            message_body = message.body.decode()
                            message_data = json.loads(message_body)
                            await self.process_messages(message_data)  # Process the message and get status
                            
                        except json.JSONDecodeError as e:
                            # print(f"Failed to decode message: {e}")
                            logger.error(f"Failed to decode message: {e}")
                            # await message.reject(requeue=False)
                            await self.publish_message_to_failed_queue({'error': 'Failed to decode message'})
                        except Exception as e:
                            print(f"Error in processing message: {e}")
                            logger.error(f"Error in processing message: {e}")
                            await self.publish_message_to_failed_queue(message_data, e)

                print(f"Started consuming from queue {self.queue_name}")
                logger.info(f"Started consuming from queue {self.queue_name}")
                await primary_queue.consume(message_handler)
                while True:
                    await asyncio.sleep(1)  # Keeps the consumer running indefinitely, can do something work too if needed
        except Exception as e:
            logger.error(f"Error while consuming messages: {e}")

queue_obj = Queue()