from models.mongo_connection import db
from bson import ObjectId
import traceback

configurationModel = db["configurations"]
version_model = db['configuration_versions']


async def get_bridge(org_id, bridge_id):
    try:
        bridge = version_model.find_one({'_id' : ObjectId(bridge_id), 'org_id' : org_id})
        return bridge
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return None

async def create_bridge_version(bridge_data):
    try:
        bridge_version_data = bridge_data
        if 'name' in bridge_version_data:
            del bridge_version_data['name']
        if 'slugName' in bridge_version_data:
            del bridge_version_data['slugName']
        if 'bridgeType' in bridge_version_data:
            del bridge_version_data['bridgeType']

        bridge_version_data['_id'] = ObjectId()
        result = version_model.insert_one(bridge_version_data)
        return  str(bridge_version_data['_id'])
    except Exception as e:
        print("error:", e)
        return {
           'success': False,
            'error': str(e)
        }
async def update_bridge(bridge_id, update_fields):
    try:
        update_query = {}

        # Handle 'versions' separately with $addToSet
        if 'versions' in update_fields:
            update_query['$addToSet'] = {'versions': {'$each': update_fields.pop('versions')}}

        # Add remaining fields to $set
        if update_fields:
            update_query['$set'] = update_fields

        updated_bridge = configurationModel.find_one_and_update(
            {'_id': ObjectId(bridge_id)},
            update_query,
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
            if 'function_ids' in updated_bridge:
                updated_bridge['function_ids'] = [str(fid) for fid in updated_bridge['function_ids']]  # Convert function_ids to string
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