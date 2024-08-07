from models.mongo_connection import db
from bson import ObjectId
import traceback

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']

async def get_bridges(bridge_id):
    
    try:
        bridges = configurationModel.find_one({'_id': ObjectId(bridge_id)})
        return {
            'success': True,
            'bridges': bridges or {},
        }
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }
    
async def get_api_call_by_name(name):
    try:
        api_call = apiCallModel.find_one({'$or': [{'function_name': name}, {'endpoint': name}]})
        return {
            'success': True,
            'apiCall': api_call
        }
    except Exception as error:
        print(f"error: {error}")
        return {
            'success': False,
            'error': "something went wrong!!"
        }

async def get_template_by_id(template_id):
    try:
        template_content = templateModel.find_one({'_id' : ObjectId(template_id)})
        return template_content
    except Exception as error : 
        print(f"template id error : {error}")
        return None

async def get_bridges_by_slug_name_and_name(slug_name, name, org_id):
    try:
        bridges = configurationModel.find_one({
            'org_id': org_id,
            '$or': [
                {'slugName': slug_name},
                {'name': name}
            ]
        })
        return {
            'success': True,
            'bridges': bridges
        }
    except Exception as error:
        print("error:", error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }
    
async def create_bridge(data):
    try:
        result = configurationModel.insert_one(data)
        return {
            'success': True,
            'bridge': {**data, '_id': result.inserted_id}
        }
    except Exception as error:
        print("error:", error)
        return {
            'success': False,
            'error': error
        }

async def get_all_bridges_in_org(org_id):
    bridges = configurationModel.find({"org_id": org_id}, {
      "_id": 1,
      "name": 1,
      "service": 1,
      "org_id": 1,
      "configuration.model": 1,
      "configuration.prompt": 1,
      "bridgeType": 1,
      "slugName":1,
    })
    bridges_list = []
    for bridge in bridges:
        bridge['_id'] = str(bridge['_id'])  # Convert ObjectId to string
        bridges_list.append(bridge)
    return bridges_list

async def get_bridge_by_id(org_id, bridge_id):
    bridge = configurationModel.find_one({'_id': ObjectId(bridge_id), 'org_id': org_id})
    if bridge:
        bridge['_id'] = str(bridge['_id'])  # Convert ObjectId to string
    return bridge


async def get_bridge_by_slugname(org_id, slug_name):
    try:
        bridge =  configurationModel.find_one({
            'slugName': slug_name,
            'org_id': org_id
        })

        if bridge and 'responseRef' in bridge:
            response_ref_id = bridge['responseRef']
            response_ref = configurationModel.find_one({'_id': response_ref_id})
            bridge['responseRef'] = response_ref

        return {
            'success': True,
            'bridges': bridge
        }
    except Exception as error:
        print("error:", error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }

async def update_bridge(bridge_id, update_fields):
    try:
        updated_bridge = configurationModel.find_one_and_update(
            {'_id': ObjectId(bridge_id)},
            {'$set': update_fields},
            return_document=True,
            upsert=True
        )

        if not updated_bridge:
            return {
                'success': False,
                'error': 'No records updated or bridge not found'
            }
        if updated_bridge:
            updated_bridge['_id'] = str(updated_bridge['_id'])  # Convert ObjectId to string
        return {
            'success': True,
            'result': updated_bridge
        }

    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': 'Something went wrong!'
        }

async def update_tools_calls(bridge_id, org_id, configuration):
    try:
        configurationModel.find_one_and_update(
            {'_id': ObjectId(bridge_id), 'org_id': org_id},
            {'$set': {
                'configuration': configuration,

            }}
        )
        return {
            'success': True,
            'message': "bridge updated successfully"
        }
    except Exception as error:
        print(f"error: {error}")
        return {
            'success': False,
            'error': "something went wrong!!"
        }