# import pika
# import json
# from config import Config

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
#             self.connection = None
#             self.channel = None
#             self._initialize_connection()
#             self.initialized = True

#     def _initialize_connection(self):
#         """Initialize RabbitMQ connection and declare the queue if not already connected."""
#         if not self.connection or self.connection.is_closed:
#             self.connection = pika.BlockingConnection(pika.URLParameters(Config.QUEUE_CONNECTIONURL))
#             self.channel = self.connection.channel()
#             self.channel.queue_declare(queue=self.queue_name, durable=True)
#             print(f"Queue '{self.queue_name}' declared and connection established.")

#     def publish_message(self, message="{'name': 'Hello'}"):
#         try:
#             if isinstance(message, dict):
#                 message = json.dumps(message)
#             # Ensure the connection and channel are active
#             self._initialize_connection()
#             # This is to make sure that the queue exists
#             # self.channel.queue_declare(queue=self.queue_name, durable=True)
#             # Publish the message
#             self.channel.basic_publish(
#                 exchange='',
#                 routing_key=self.queue_name,
#                 body=message,
#                 properties=pika.BasicProperties(
#                     delivery_mode=pika.DeliveryMode.Persistent,  # make message persistent
#                 )
#             )
#             print(f"Message published to {self.queue_name}")
#         except Exception as e:
#             print(f"Failed to publish message: {e}")

#     def process_messages(self, messages):
#         """Implement your batch processing logic here."""
#         print(f"Processing batch of {len(messages)} messages")
#         for message in messages:
#             print("Message:", message)

#     def consume_messages(self, batch_size=20):
#         try:
#             # Ensure the connection and channel are active
#             self._initialize_connection()
#             # This is to make sure that the queue exists
#             # self.channel.queue_declare(queue=self.queue_name, durable=True)
#             messages = []
            
#             def callback(ch, method, properties, body):
#                 print(f" [x] Received ")
#                 try:
#                     message = json.loads(body)
#                     messages.append(message)
                    
#                     if len(messages) >= batch_size:
#                         self.process_messages(messages)
#                         messages.clear()
#                     ch.basic_ack(delivery_tag=method.delivery_tag)
#                 except json.JSONDecodeError as e:
#                     print(f"Failed to decode message: {e}")
#                     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
#                 except Exception as e:
#                     print(f"Error in processing message: {e}")
#                     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
#             self.channel.basic_qos(prefetch_count=batch_size)
#             self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback)

#             print("Starting message consumption")
#             self.channel.start_consuming()
#         except Exception as e:
#             print(f"Error while consuming messages: {e}")
#             # if self.connection and self.connection.is_open:
#             #     self.connection.close()
#             #     print("Connection closed after consuming error.")


import asyncio
import aio_pika
import json
from config import Config

class Queue:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Queue, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Ensure initialization happens only once
            print("Queue Service Initialized")
            self.queue_name = Config.QUEUE_NAME
            self.connection = None
            self.channel = None
            self.initialized = True

    async def _initialize_connection(self):
        """Initialize RabbitMQ connection and declare the queue if not already connected."""
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(Config.QUEUE_CONNECTIONURL)
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.queue_name, durable=True)
            print(f"Queue '{self.queue_name}' declared and connection established.")

    async def publish_message(self, message={'name': 'Hello'}):
        try:
            # Ensure the connection and channel are active
            await self._initialize_connection()
            # Check if the channel is open before publishing
            if self.channel.is_closed:
                raise Exception("Channel is closed, cannot publish message.")
            # Publish the message
            message_body = json.dumps(message)
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=message_body.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=self.queue_name,
            )
            print(f"Message published to {self.queue_name}")
        except Exception as e:
            print(f"Failed to publish message: {e}")

    async def process_messages(self, messages):
        """Implement your batch processing logic here."""
        print(f"Processing batch of {len(messages)} messages")
        for message in messages:
            print("Message:", message)

    async def consume_messages(self, batch_size=20):
        try:
            # Ensure the connection and channel are active
            await self._initialize_connection()
            queue = await self.channel.declare_queue(self.queue_name, durable=True)
            messages = []
            print('start consuming')
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            print(f" [x] Received {message.body.decode()}")
                            decoded_message = json.loads(message.body.decode())
                            messages.append(decoded_message)

                            # Process the batch when it reaches the defined batch size
                            if len(messages) >= batch_size:
                                await self.process_messages(messages)
                                messages.clear()
                        except json.JSONDecodeError as e:
                            print(f"Failed to decode message: {e}")
                            await message.reject(requeue=False)
                        except Exception as e:
                            print(f"Error in processing message: {e}")
                            await message.reject(requeue=False)
        except Exception as e:
            print(f"Error while consuming messages: {e}")
