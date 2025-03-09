from models.mongo_connection import db
configurationModel = db["configurations"]

testcases_model = db['testcases']
testcases_history_model = db['testcases_history']


async def get_testcases(bridge_id): 
    return await testcases_model.find({'bridge_id': bridge_id}).to_list(length = None)

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
