from models.mongo_connection import db
configurationModel = db["configurations"]
from globals import *
from bson import ObjectId
import datetime

testcases_model = db['testcases']
testcases_history_model = db['testcases_history']


async def get_testcases(bridge_id): 
    return await testcases_model.find({'bridge_id': bridge_id}).to_list(length = None)

async def create_testcase(testcase_data):
    """Create a new testcase"""
    testcase_data['created_at'] = datetime.datetime.utcnow()
    testcase_data['updated_at'] = datetime.datetime.utcnow()
    result = await testcases_model.insert_one(testcase_data)
    return result

async def delete_testcase_by_id(testcase_id):
    """Delete a testcase by _id"""
    try:
        object_id = ObjectId(testcase_id)
        result = await testcases_model.delete_one({'_id': object_id})
        return result
    except Exception as e:
        logger.error(f"Error deleting testcase: {str(e)}")
        raise e

async def get_all_testcases_by_bridge_id(bridge_id):
    """Get all testcases for a specific bridge_id"""
    return await testcases_model.find({'bridge_id': bridge_id}).to_list(length=None)

async def create_testcases_history(data):
    result =  await testcases_history_model.insert_many(data)
    for obj in data:
        obj['_id'] = str(obj['_id'])
    return result

async def fetch_testcases_history(bridge_id):
    pipeline = [
        {"$match": {"bridge_id": bridge_id}},
        {"$lookup": {
            "from": "testcases_history",
            "let": {"testcaseIdStr": {"$toString": "$_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$testcase_id", "$$testcaseIdStr"]}}}
            ],
            "as": "history"
        }}
    ]
    
    cursor = testcases_model.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result

async def delete_current_testcase_history(version_id):
    try:
        
        pipeline = [
            {"$match": {"version_id": version_id}},
            {"$sort": {"testcase_id": 1, "created_at": -1}},
            {
                "$group": {
                    "_id": "$testcase_id",
                    "latest_id": {"$first": "$_id"}
                }
            },
            {"$project": {"_id": 0, "latest_id": 1}}
        ]

        # Get IDs of latest entries
        cursor = testcases_history_model.aggregate(pipeline)
        latest_ids = [doc["latest_id"] async for doc in cursor]

        # Delete all other entries for the given version_id
        await testcases_history_model.delete_many({"version_id": version_id, "_id": {"$nin": latest_ids}})
    except Exception as e: 
        logger.error(f"Error in deleting current testcase history: {str(e)}")
        traceback.print_exc()