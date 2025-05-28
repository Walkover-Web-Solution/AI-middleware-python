import asyncio
import json
from aio_pika import connect_robust, Message, DeliveryMode, RobustConnection
from aio_pika.abc import AbstractIncomingMessage
from config import Config
from src.services.utils.logger import logger

# Singleton Connection Manager
class ConnectionManager:
    _instance = None
    connection: RobustConnection = None
    channels = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_connection(self) -> RobustConnection:
        if not self.connection or self.connection.is_closed:
            self.connection = await connect_robust(Config.QUEUE_CONNECTIONURL)
            logger.info("New RabbitMQ connection established")
        return self.connection

    async def get_channel(self, queue_name: str):
        if queue_name not in self.channels or self.channels[queue_name].is_closed:
            connection = await self.get_connection()
            self.channels[queue_name] = await connection.channel()
            logger.info(f"New channel created for {queue_name}")
        return self.channels[queue_name]

    async def close(self):
        for name, channel in self.channels.items():
            await channel.close()
            logger.info(f"Closed channel for {name}")
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection")
        self.connection = None
        self.channels = {}

# Base Queue Class with Shared Functionality
class BaseQueue:
    def __init__(self, queue_name, failed_queue_suffix="-Failed"):
        if not hasattr(self, 'initialized'):
            self.queue_name = queue_name
            self.failed_queue_name = f"{self.queue_name}{failed_queue_suffix}"
            self.prefetch_count = Config.PREFETCH_COUNT or 50
            self.connection_manager = ConnectionManager()
            self.channel = None
            self.initialized = True
            self.queues_declared = False

    async def connect(self):
        try:
            if not self.channel or self.channel.is_closed:
                self.channel = await self.connection_manager.get_channel(self.queue_name)
            return True
        except Exception as E:
            logger.error(f"Connection error for {self.queue_name}: {E}")
            return False

    async def disconnect(self):
        if self.channel:
            await self.channel.close()
            self.channel = None

    async def create_queue_if_not_exists(self):
        try:
            if not self.queues_declared and await self.connect():
                await self.channel.declare_queue(self.queue_name, durable=True)
                await self.channel.declare_queue(self.failed_queue_name, durable=True)
                logger.info(f"Queues declared: {self.queue_name}, {self.failed_queue_name}")
                self.queues_declared = True
        except Exception as e:
            logger.error(f"Queue declaration failed: {e}")
            raise

    async def publish_message(self, message, queue_name=None):
        try:
            await self.connect()
            target_queue = queue_name or self.queue_name
            message_body = json.dumps(message)
            await self.channel.default_exchange.publish(
                Message(
                    body=message_body.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    headers={'retry_count': 1}
                ),
                routing_key=target_queue,
            )
            logger.info(f"Message published to {target_queue}")
        except Exception as e:
            logger.error(f"Publish failed to {target_queue}: {e}")
            raise

    async def _message_handler_wrapper(self, message: AbstractIncomingMessage, process_callback):
        async with message.process():
            try:
                message_body = message.body.decode()
                message_data = json.loads(message_body)
                await process_callback(message_data)
            except json.JSONDecodeError as e:
                logger.error(f"Message decode error: {e}")
                await self.publish_message(
                    {'error': 'Failed to decode message', 'original': message.body.decode()},
                    self.failed_queue_name
                )
            except Exception as e:
                logger.error(f"Processing error: {e}")
                await self.publish_message(
                    {'error': str(e), 'original': message_data},
                    self.failed_queue_name
                )