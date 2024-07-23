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
    
async def get_api_call_by_id(api_id):
    try:
        api_call = apiCallModel.find_one({'_id': ObjectId(api_id)})
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
        
# async def get_bridge_by_slugname(org_id, slug_name):
#     try:
#         print(111,org_id,222,slug_name)
#         bridges = configurationModel.find_one({
#             'slugName': slug_name,
#             'org_id': 'husain_123'
#         })
#         print("hii hello", bridges)
#         if bridges and 'responseRef' in bridges:
#             # Populate 'responseRef' if it's a reference to another collection
#             print("hii 3")
#             response_ref = await db['responses'].find_one({'_id': bridges['responseRef']})
#             bridges['responseRef'] = response_ref
        
#         return {
#             'success': True,
#             'bridges': bridges
#         }
#     except Exception as error:
#         traceback.print_exc()
#         print(f"error: {error}")
#         return {
#             'success': False,
#             'error': "something went wrong!!"
#         }


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
            'error': "something went wrong!!"
        }


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