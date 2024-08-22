from models.mongo_connection import db
from bson.json_util import dumps, loads

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']

async def get_api_calls(org_id):
    try:
        pipeline = [
            {'$match': {'org_id': org_id}},
            {'$addFields': {
                '_id': {'$toString': '$_id'},
                'bridge_ids': {'$map': {
                    'input': '$bridge_ids',
                    'as': 'bridge_id',
                    'in': {'$toString': '$$bridge_id'}
                }},
                'created_at': {'$dateToString': {'format': '%Y-%m-%d %H:%M:%S', 'date': '$created_at'}},
                'updated_at': {'$dateToString': {'format': '%Y-%m-%d %H:%M:%S', 'date': '$updated_at'}}
            }}
        ]
        api_calls = list(apiCallModel.aggregate(pipeline))
        return api_calls or []
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "Error in getting api calls of a organization!!"
        }