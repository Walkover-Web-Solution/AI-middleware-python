from models.mongo_connection import db
configurationModel = db["configurations"]
from globals import *

testcases_model = db['testcases']
testcases_history_model = db['testcases_history']


async def get_testcases(bridge_id): 
    """Return all testcases linked to a bridge."""
    return await testcases_model.find({'bridge_id': bridge_id}).to_list(length = None)

async def create_testcases_history(data):
    """Insert many testcase history records and mirror ids back into input."""
    result =  await testcases_history_model.insert_many(data)
    for obj in data:
        obj['_id'] = str(obj['_id'])
    return result

async def fetch_testcases_history(bridge_id):
    """Aggregate testcases with their execution history."""
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
    """Keep only the latest history entry per testcase for a version."""
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
