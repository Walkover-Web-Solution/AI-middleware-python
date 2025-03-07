from models.mongo_connection import db
configurationModel = db["configurations"]

testcases_model = db['testcases']


async def get_testcases(bridge_id): 
    return await testcases_model.find({'bridge_id': bridge_id}).to_list(length = None)