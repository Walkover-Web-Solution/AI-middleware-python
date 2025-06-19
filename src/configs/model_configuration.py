import asyncio
import time
from pymongo.errors import OperationFailure, PyMongoError
from src.services.utils.load_model_configs import get_model_configurations
from models.mongo_connection import db
from src.services.utils.logger import logger
from globals import *

modelConfigModel = db["modelconfigurations"]
model_config_document = {}

async def init_model_configuration():
    """Initializes or refreshes the model configuration document."""
    global model_config_document
    try:
        new_document = await get_model_configurations()
        model_config_document.clear() # Clear old config before updating
        model_config_document.update(new_document)
        logger.info("Model configurations refreshed successfully.")
    except Exception as e:
        logger.error(f"Error refreshing model configurations: {e}")

async def _async_change_listener():
    """The core async change stream listener."""
    pipeline = [{"$match": {"operationType": {"$in": ["insert", "update", "replace"]}}}]
    try:
        async with modelConfigModel.watch(pipeline) as stream:
            logger.info("MongoDB change stream is now listening for model configuration changes.")
            async for change in stream:
                logger.info(f"Change detected in model configurations: {change['operationType']}")
                await init_model_configuration()
    except OperationFailure as e:
        logger.error(f"Change stream operation failed: {e}")
        raise # Re-raise to be caught by the sync wrapper
    except Exception as e:
        logger.error(f"An unexpected error occurred in the async listener: {e}")
        raise

def listen_for_changes():
    """A synchronous wrapper for the change stream listener with a retry loop."""
    while True:
        try:
            asyncio.run(_async_change_listener())
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"MongoDB connection error in change stream: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"An unexpected error occurred in listen_for_changes: {e}. Restarting in 10 seconds...")
            time.sleep(10)

