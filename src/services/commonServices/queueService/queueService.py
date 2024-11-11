import asyncio
from aio_pika import connect_robust, Message, DeliveryMode, RobustConnection, ExchangeType
from aio_pika.abc import AbstractRobustConnection
import json
from config import Config
from src.services.commonServices.common import chat
from concurrent.futures import ThreadPoolExecutor
from aio_pika.abc import AbstractIncomingMessage
from src.services.utils.logger import logger

executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)
class Queue:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Queue, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Ensure initialization happens only once
            print("Queue Service Initialized")
            self.queue_name = Config.QUEUE_NAME or "AI-MIDDLEARE-DEFAULT"
            self.failed_queue_name = f"{self.queue_name}-Failed"
            # self.failed_exchange_name = f"{self.failed_queue_name}-exchange"
            self.binding_key = None
            self.initialized = True
            self.connection_url = Config.QUEUE_CONNECTIONURL
            self.prefetch_count = Config.PREFETCH_COUNT or 50
            self.connection = None
            self.channel = None
            self.initialized = True
            self.queues_declared = False
            
    async def connect(self):
        try:
            if not self.connection or self.connection.is_closed:
                self.connection: RobustConnection = await connect_robust(self.connection_url)
                self.channel = await self.connection.channel()
                # print(f"Channel created and connection established.")
                logger.info(f"Channel created and connection established.")
            return True
        except Exception as E:
            # print(f"Error while connecting to RabbitMQ: {E}")
            logger.error(f"Error while connecting to RabbitMQ: {E}")
            return False
        

    async def disconnect(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        self.connection = None
        self.channel = None
            

    async def create_queue_if_not_exists(self):
        try:
            if not self.queues_declared and await self.connect():
                # for queue_name in self.consumer_map.keys():
                #     await self.channel.declare_queue(queue_name, durable=True)
                await self.channel.declare_queue(self.queue_name, durable=True)
                print(f"Queue {self.queue_name} declared")
                
                # failed_exchange = await self.channel.declare_exchange(
                #     self.failed_exchange_name, ExchangeType.DIRECT, durable=True
                # )
                await self.channel.declare_queue(self.failed_queue_name, durable=True)
                print(f"Queue {self.failed_queue_name} declared")
                # await failed_queue.bind(failed_exchange, routing_key=self.failed_queue_name)
                # print(f"Queue {self.failed_queue_name} declared and bound to {self.failed_exchange_name}")
                self.queues_declared = True
        except Exception as e:
            print(f"Failed to declare queue: {e}")
            raise ValueError(f"Failed to declare queue: {e}")
            
            
    async def publish_message(self, message={'name': 'Hello'}):
        try:
            # Ensure the connection and channel are active
            await self.connect()
            # Check if the channel is open before publishing
            if self.channel.is_closed:
                raise Exception("Channel is closed, cannot publish message.")
            # Publish the message
            message_body = json.dumps(message)
            await self.channel.default_exchange.publish(
                Message(body=message_body.encode(), delivery_mode=DeliveryMode.PERSISTENT, headers={'retry_count': 1}),
                routing_key=self.queue_name,
            )
            print(f"Message published to {self.queue_name}")
        except Exception as e:
            print(f"Failed to publish message ===: {e}")
            raise ValueError(f"Failed to publish message ===: {e}")
         
         
    async def publish_message_to_failed_queue(self, message={'name': 'Hello'}):
        try:
            # Ensure the connection and channel are active
            await self.connect()
            # Check if the channel is open before publishing
            if self.channel.is_closed:
                raise Exception("Channel is closed, cannot publish message.")
            # Publish the message
            message_body = json.dumps(message)
            # failed_exchange = await self.channel.get_exchange(self.failed_exchange_name)
            await self.channel.default_exchange.publish(
                Message(body=message_body.encode(), delivery_mode=DeliveryMode.PERSISTENT),
                routing_key=self.failed_queue_name,
            )
            print(f"Message published to {self.failed_queue_name}")
        except Exception as e:
            print(f"Failed to publish message ===: {e}")
            raise ValueError(f"Failed to publish message ===: {e}")
        

    async def process_messages(self, messages):
        """Implement your batch processing logic here."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, lambda: asyncio.run(chat(messages)))

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
                            await self.publish_message_to_failed_queue(message_data)

                print(f"Started consuming from queue {self.queue_name}")
                logger.info(f"Started consuming from queue {self.queue_name}")
                await primary_queue.consume(message_handler)
                while True:
                    await asyncio.sleep(1)  # Keeps the consumer running indefinitely, can do something work too if needed
        except Exception as e:
            # print(f"Error while consuming messages: {e}")
            logger.error(f"Error while consuming messages: {e}")

queue_obj = Queue()