from models.connection import db
from bson import ObjectId
import traceback

configurationModel = db["configurations"]
apiCallModel = db['apicalls']

async def get_bridges(bridge_id):
    try:
        bridges = configurationModel.find_one({'_id': ObjectId(bridge_id)})
        return {
            'success': True,
            'bridges': bridges,
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
    
async def get_bridge_by_slugname(org_id, slug_name):
    try:
        # Assuming the use of Motor, an async driver for MongoDB
        bridges = await configurationModel.find_one({
            'slugName': slug_name,
            'org_id': org_id
        })
        
        if bridges and 'responseRef' in bridges:
            # Populate 'responseRef' if it's a reference to another collection
            response_ref = await db['responses'].find_one({'_id': bridges['responseRef']})
            bridges['responseRef'] = response_ref
        
        return {
            'success': True,
            'bridges': bridges
        }
    except Exception as error:
        print(f"error: {error}")
        return {
            'success': False,
            'error': "something went wrong!!"
        }
