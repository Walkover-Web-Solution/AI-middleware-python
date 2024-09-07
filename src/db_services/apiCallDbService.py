from models.mongo_connection import db
from bson.json_util import dumps, loads

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']

# todo :: to make it more better
async def get_all_api_calls_by_org_id(org_id):
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
                'created_at': {
                    '$cond': {
                        'if': {'$eq': [{'$type': '$created_at'}, 'string']},
                        'then': '$created_at',
                        'else': {'$dateToString': {'format': '%Y-%m-%d %H:%M:%S', 'date': '$created_at'}}
                    }
                },
                'updated_at': {
                    '$cond': {
                        'if': {'$eq': [{'$type': '$updated_at'}, 'string']},
                        'then': '$updated_at',
                        'else': {'$dateToString': {'format': '%Y-%m-%d %H:%M:%S', 'date': '$updated_at'}}
                    }
                }
            }}
        ]
        api_calls = list(apiCallModel.aggregate(pipeline))
        
        for index, api_data in enumerate(api_calls):
            fields = api_data['fields']
            transformed_data = {}
            if not fields:  # Check if fields is empty or null
                transformed_data = {}
            elif api_data.get("version") != "v2":
                transformed_data = {
                    item["variable_name"]: {
                        "description": item["description"], 
                        "enum": [] if(item["enum"] == '') else item.get("enum", []),
                        "type": "string",
                        "parameter": {}
                    } for item in fields}
            api_calls[index]['fields'] = transformed_data
        return api_calls or []
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "Error in getting api calls of a organization!!"
        }