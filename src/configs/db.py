from motor.motor_asyncio import AsyncIOMotorClient

class MongoDBSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            # Initialize MongoDB client asynchronously
            cls._instance.client = AsyncIOMotorClient(Config.MONGODB_CONNECTION_URI)
        return cls._instance

    @classmethod
    def get_client(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance.client


# from your_module import MongoDBSingleton
mongo_client = MongoDBSingleton.get_client()