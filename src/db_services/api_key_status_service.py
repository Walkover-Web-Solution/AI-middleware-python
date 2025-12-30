from bson import ObjectId
from globals import logger
from models.mongo_connection import db

apikeyCredentialsModel = db["apikeycredentials"]

async def update_apikey_status(apikey_id: str, status: str):
    if not apikey_id:
        return

    try:
        result = await apikeyCredentialsModel.update_one(
            {"_id": ObjectId(apikey_id)},
            {"$set": {"status": status}}
        )
        if not result.modified_count:
            logger.warning(f"No apikey credential updated for id={apikey_id}")
    except Exception as exc:
        logger.error(f"Failed to update API key status for {apikey_id}: {exc}")