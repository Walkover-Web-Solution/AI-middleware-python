
import asyncio
import importlib
import json
import subprocess
import time
from collections import defaultdict
from aio_pika.abc import AbstractIncomingMessage
from aio_pika import connect_robust, Message
from config import Config
from components.config import RABBIT_URL, CONSUMER_MAP_JSON, ENVIRONMENT, REPORTS_RABBITMQ_URL, REPORTS_MAP_JSON


class QueueManager:
    connection = None
    channel = None
    queues_declared = False
    consumers = defaultdict(list)

    def __init__(self, rabbit_url, consumer_map = '{}'):
        self.connection_url = Config.QUEUE_CONNECTIONURL
        self.queue_name = Config.QUEUE_NAME
        self.consumer_map = json.loads(consumer_map)

    async def connect(self):
        try:
            if not self.connection or self.connection.is_closed:
                self.connection = await connect_robust(self.connection_url)
                self.channel = await self.connection.channel()
            return True
        except Exception as E:
            print(f"Error while connecting to RabbitMQ: {E}")
            return False

    async def disconnect(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

    async def create_queue_if_not_exists(self):
        if not self.queues_declared and await self.connect():
            # for queue_name in self.consumer_map.keys():
            #     await self.channel.declare_queue(queue_name, durable=True)
            await self.channel.declare_queue(self.qu, durable=True)
            self.queues_declared = True

    async def initialize_consumers(self):
        if await self.connect():
            for queue_name, limits in self.consumer_map.items():
                app_name = limits.get('app_name', "customBot")
                for num in range(limits['min']):
                    await self.consumer_process(app_name, queue_name, "start", num)
                    # logger.info(f"Started consumer for {queue_name}. Current: {len(self.consumers[queue_name])}")
                    print(f"Started consumer for {queue_name}. Current: {len(self.consumers[queue_name])}")
                    

    async def terminate_consumers(self):
        if await self.connect():
            for queue_name, limits in self.consumer_map.items():
                app_name = limits.get('app_name', "customBot")
                for _ in range(len(self.consumers[queue_name])):
                    await self.consumer_process(app_name, queue_name, "stop")
                    print(f"Stopped consumer for {queue_name}. Current: {len(self.consumers[queue_name])}")
            print("Stopped All consumer and Disconnected")

    async def consumer_process(self, app_name, queue_name, action, consumer_no=None):
        if action == "start":
            command = ['python', 'consumer.py', app_name, queue_name, str(consumer_no)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.consumers[queue_name].append(process)
            print(f"Started consumer process for {queue_name}. PID: {process.pid}")
        elif action == "stop":
            processes = self.consumers[queue_name]
            if processes:
                process = processes.pop()
                process.terminate()
                # logger.info(f"Stopped consumer process for {queue_name}. PID: {process.pid}")
                print(f"Stopped consumer process for {queue_name}. PID: {process.pid}")
            else:
                # logger.info(f"No active consumer process found for {queue_name}")
                print(f"No active consumer process found for {queue_name}")
        else:
            print(f"Invalid active given, Expected - start, stop : Given - {action}")

    async def adjust_consumer_count(self):
        start_time = time.time()
        if await self.connect():
            for queue_name in self.consumer_map.keys():
                data_count = await self.get_queue_data_count(queue_name)
                # Determine consumer count based on predefined thresholds
                app_name = self.consumer_map[queue_name].get('app_name', "customBot")
                current_consumers = len(self.consumers[queue_name])
                expected_consumers = max(self.consumer_map[queue_name]["min"],
                                         min(data_count // 100, self.consumer_map[queue_name]["max"]))
                if expected_consumers > current_consumers:
                    await self.consumer_process(app_name, queue_name, "start", current_consumers + 1)
                    # logger.info(f"Increased consumer for {queue_name}. Total: {len(self.consumers[queue_name])}")
                    print(f"Increased consumer for {queue_name}. Total: {len(self.consumers[queue_name])}")
                elif expected_consumers < current_consumers:
                    await self.consumer_process(app_name, queue_name, "stop")
                    # logger.info(f"Decreased consumer for {queue_name}. Total: {len(self.consumers[queue_name])}")
                    print(f"Decreased consumer for {queue_name}. Total: {len(self.consumers[queue_name])}")

                for num, process in enumerate(self.consumers[queue_name]):
                    if process.poll() is not None:  # Process has terminated
                        # logger.warning(f"Consumer process for {queue_name} with PID {process.pid} terminated with return code {process.poll()}")
                        print(f"Consumer process for {queue_name} with PID {process.pid} terminated with return code {process.poll()}")
                        self.consumers[queue_name].remove(process)
                        process.terminate()
                        await self.consumer_process(app_name, queue_name, "start", num)
                        # logger.info(f"Restart 1 consumer for {queue_name}. Total: {len(self.consumers[queue_name])}")
                        print(f"Restart 1 consumer for {queue_name}. Total: {len(self.consumers[queue_name])}")

    async def get_queue_data_count(self, queue_name: str):
        if await self.connect():
            queue = await self.channel.declare_queue(queue_name, durable=True)
            message_count = queue.declaration_result.message_count
            return message_count

    async def publish_message(self, queue_name: str, module: str, method: str, args: list = None, kwargs: dict = None,
                              message: dict = None, modify_queue_name: bool = True):
        queue_name = f"bot_{queue_name}_{ENVIRONMENT[0:4]}" if modify_queue_name else queue_name
        if not message:
            message = {
                "module": module,
                "method": method,
                "args": [],
                "kwargs": {}
            }
            if args is not None:
                message['args'] = args
            if kwargs is not None:
                message['kwargs'] = kwargs
        await self.connect()
        await self.channel.default_exchange.publish(
            Message(body=json.dumps(message).encode()),
            routing_key=queue_name
        )

    async def publish_message_with_delay(self, queue_name: str, module: str, method: str, args: list = None,
                                         kwargs: dict = None, message: dict = None, modify_queue_name: bool = True,
                                         delay_ms: int = 0):

        queue_name = f"bot_{queue_name}_{ENVIRONMENT[0:4]}" if modify_queue_name else queue_name
        if not message:
            message = {
                "module": module,
                "method": method,
                "args": args if args is not None else [],
                "kwargs": kwargs if kwargs is not None else {}
            }

        await self.connect()

        delay_queue_name = f"delay_{delay_ms}_{queue_name}"
        await self.channel.declare_queue(
            delay_queue_name,
            arguments={
                "x-expires": delay_ms + 10000,
                "x-message-ttl": delay_ms,
                "x-dead-letter-exchange": self.channel.default_exchange.name,
                "x-dead-letter-routing-key": queue_name
            }
        )

        await self.channel.default_exchange.publish(
            Message(body=json.dumps(message).encode()),
            routing_key=delay_queue_name
        )

    async def consume_message(self, app_name, queue_name):
        if await self.connect():
            await self.channel.set_qos(prefetch_count=10)
            queue = await self.channel.get_queue(queue_name)

            async def message_handler(message: AbstractIncomingMessage):
                async with message.process():
                    try:
                        message_body = message.body.decode()
                        message_data = json.loads(message_body)
                        module_name = message_data.get("module")
                        class_name = module_name[0].upper() + module_name[1:]
                        method_name = message_data.get("method")
                        args = message_data.get("args", [])
                        kwargs = message_data.get("kwargs", {})

                        # Dynamically import the class and call the method
                        module = importlib.import_module(f"apps.{app_name}.bgtasks.{module_name}")
                        klass = getattr(module, class_name)
                        method = getattr(klass, method_name)
                        if method:
                            await method(*args, **kwargs)
                            # TODO : Check It :await asyncio.wait_for(method(*args, **kwargs), 60)
                        else:
                            # logger.error(f"Method {method_name} not found")
                            print(f"Method {method_name} not found")
                    except Exception as E:
                        # logger.exception(E)
                        print(E)
                        from components.services.alertServices import AlertServices
                        AlertServices.slack_alert(str(E), "message_handler", "Consumer Error", json.loads(message.body.decode()))

            # logger.info(f"Started consuming from queue {queue_name}")
            print(f"Started consuming from queue {queue_name}")
            await queue.consume(message_handler)
            while True:
                await asyncio.sleep(1)  # Keeps the consumer running indefinitely, can do something work too if needed


queue_manager = QueueManager(RABBIT_URL, CONSUMER_MAP_JSON)
# reports_queue_manager = QueueManager(REPORTS_RABBITMQ_URL, REPORTS_MAP_JSON)








# import asyncio
# from aio_pika import connect_robust, Message, DeliveryMode, ExchangeType
# import json
# from config import Config
# from src.services.commonServices.common import chat  # Ensure this accepts a dict
# from concurrent.futures import ThreadPoolExecutor
# from typing import List, Dict, Any

# executor = ThreadPoolExecutor(max_workers=int(Config.max_workers) or 10)

# class Queue:
#     _instance = None

#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             cls._instance = super(Queue, cls).__new__(cls, *args, **kwargs)
#         return cls._instance

#     def __init__(self):
#         if not hasattr(self, 'initialized'):  # Ensure initialization happens only once
#             print("Queue Service Initialized")
#             self.queue_name = Config.QUEUE_NAME
#             self.retry_queue_name = f"{self.queue_name}_retry"
#             self.dlq_name = f"{self.queue_name}_dlq"
#             self.exchange_name = Config.QUEUE_EXCHANGE_NAME
#             self.connection_url = Config.QUEUE_CONNECTIONURL
#             self.connection = None
#             self.channel = None
#             self.initialized = True
#             self.queues_declared = False

#     async def connect(self):
#         try:
#             if not self.connection or self.connection.is_closed:
#                 self.connection = await connect_robust(self.connection_url)
#                 self.channel = await self.connection.channel()
#                 # Set prefetch to handle concurrency
#                 await self.channel.set_qos(prefetch_count=10)
#                 print(f"Connected to RabbitMQ at {self.connection_url}")
#             return True
#         except Exception as E:
#             print(f"Error while connecting to RabbitMQ: {E}")
#             return False

#     async def disconnect(self):
#         if self.channel:
#             await self.channel.close()
#         if self.connection:
#             await self.connection.close()

#     async def create_queues(self):
#         if not self.queues_declared and await self.connect():
#             # Declare main exchange
#             exchange = await self.channel.declare_exchange(
#                 self.exchange_name, ExchangeType.DIRECT, durable=True
#             )

#             # Declare DLX
#             dlx_exchange = await self.channel.declare_exchange(
#                 f"{self.exchange_name}_dlx", ExchangeType.DIRECT, durable=True
#             )

#             # Declare main queue with DLX settings
#             main_queue = await self.channel.declare_queue(
#                 self.queue_name,
#                 durable=True,
#                 arguments={
#                     'x-dead-letter-exchange': f"{self.exchange_name}_dlx",
#                     'x-dead-letter-routing-key': self.retry_queue_name
#                 }
#             )
#             await main_queue.bind(exchange, routing_key=self.queue_name)

#             # Declare retry queue with TTL and DLX settings
#             retry_queue = await self.channel.declare_queue(
#                 self.retry_queue_name,
#                 durable=True,
#                 arguments={
#                     'x-message-ttl': Config.RETRY_DELAY_MS,  # e.g., 5000 for 5 seconds
#                     'x-dead-letter-exchange': self.exchange_name,
#                     'x-dead-letter-routing-key': self.queue_name
#                 }
#             )
#             await retry_queue.bind(dlx_exchange, routing_key=self.retry_queue_name)

#             # Declare DLQ
#             dlq = await self.channel.declare_queue(
#                 self.dlq_name,
#                 durable=True
#             )
#             await dlq.bind(dlx_exchange, routing_key=self.dlq_name)

#             self.queues_declared = True
#             print("All queues and exchanges have been declared.")

#     async def publish_message(self, message: Dict[str, Any]):
#         """
#         Publishes a message to the main queue.
#         """
#         try:
#             # Ensure the connection and channel are active
#             await self.connect()
#             await self.create_queues()

#             # Check if the channel is open before publishing
#             if self.channel.is_closed:
#                 raise Exception("Channel is closed, cannot publish message.")

#             # Publish the message with initial retry_count
#             message_body = json.dumps(message)
#             await self.channel.default_exchange.publish(
#                 Message(
#                     body=message_body.encode(),
#                     delivery_mode=DeliveryMode.PERSISTENT,
#                     headers={'retry_count': 0}  # Initialize retry count
#                 ),
#                 routing_key=self.queue_name,
#             )
#             print(f"Message published to {self.queue_name}")
#         except Exception as e:
#             print(f"Failed to publish message: {e}")
#             raise  # Re-raise exception for higher-level handling

#     async def process_messages(self, messages: List[Dict[str, Any]]):
#         """
#         Implements your batch processing logic.
#         """
#         print(f"Processing batch of {len(messages)} messages")
#         for message in messages:
#             try:
#                 # Run the chat function in a thread pool to avoid blocking
#                 # Ensure 'chat' can handle a dict input
#                 await asyncio.get_event_loop().run_in_executor(
#                     executor, 
#                     lambda: asyncio.run(chat(message))  # Assuming chat is async and handles dict
#                 )
#             except Exception as e:
#                 print(f"Error processing message: {e}")
#                 raise  # Let the caller handle the exception

#     async def consume_messages(self, batch_size=20, max_retries=5):
#         """
#         Consumes messages from the main queue in batches and handles retries.
#         """
#         try:
#             # Ensure the connection and channel are active
#             await self.connect()
#             await self.create_queues()
#             queue = await self.channel.declare_queue(self.queue_name, durable=True)
#             messages = []
#             print('Start consuming')

#             async with queue.iterator() as queue_iter:
#                 async for message in queue_iter:
#                     async with message.process():
#                         try:
#                             print(f" [x] Received message")
#                             message_body = message.body.decode()
#                             message_data = json.loads(message_body)

#                             # Retrieve retry count from headers
#                             headers = message.headers or {}
#                             retry_count = headers.get('retry_count', 0)

#                             if retry_count >= max_retries:
#                                 print(f"Message reached max retries. Sending to DLQ.")
#                                 # Reject without requeue to send to DLQ
#                                 await message.reject(requeue=False)
#                                 continue

#                             messages.append(message_data)

#                             if len(messages) >= batch_size:
#                                 try:
#                                     await self.process_messages(messages)
#                                     messages.clear()
#                                 except Exception as e:
#                                     print(f"Error processing batch: {e}")
#                                     # Increment retry count and republish to retry queue
#                                     for msg in messages:
#                                         await self.publish_retry_message(msg, retry_count + 1)
#                                     messages.clear()
#                         except json.JSONDecodeError as e:
#                             print(f"Failed to decode message: {e}")
#                             await message.reject(requeue=False)
#                         except Exception as e:
#                             print(f"Error in processing message: {e}")
#                             await message.reject(requeue=False)
#             # Keeps the consumer running indefinitely
#             while True:
#                 await asyncio.sleep(1)
#         except Exception as e:
#             print(f"Error while consuming messages: {e}")
#             # Optionally, implement reconnection logic here

#     async def publish_retry_message(self, message: Dict[str, Any], retry_count: int):
#         """
#         Publishes a message to the retry queue with an incremented retry count.
#         """
#         try:
#             message_body = json.dumps(message)
#             await self.channel.default_exchange.publish(
#                 Message(
#                     body=message_body.encode(),
#                     delivery_mode=DeliveryMode.PERSISTENT,
#                     headers={'retry_count': retry_count}
#                 ),
#                 routing_key=self.retry_queue_name,
#             )
#             print(f"Message republished to retry queue with retry_count={retry_count}")
#         except Exception as e:
#             print(f"Failed to republish message to retry queue: {e}")
#             raise  # Re-raise exception for higher-level handling
