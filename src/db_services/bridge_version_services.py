from models.mongo_connection import db
from bson import ObjectId
import traceback
import json
import asyncio
from src.services.utils.apiservice import fetch

configurationModel = db["configurations"]
version_model = db['configuration_versions']


async def get_version(org_id, version_id):
    try:
        bridge = version_model.find_one({'_id' : ObjectId(version_id), 'org_id' : org_id})
        return bridge
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return None

async def create_bridge_version(bridge_data, parent_id=None):
    try:
        bridge_version_data = bridge_data.copy()
        if 'name' in bridge_version_data:
            del bridge_version_data['name']
        if 'slugName' in bridge_version_data:
            del bridge_version_data['slugName']
        if 'bridgeType' in bridge_version_data:
            del bridge_version_data['bridgeType']
        bridge_version_data['is_drafted'] = True
        bridge_version_data['parent_id'] = parent_id or str(bridge_data['_id'])
        bridge_version_data['_id'] = ObjectId()
        version_model.insert_one(bridge_version_data)
        return str(bridge_version_data['_id'])
    except Exception as e:
        print("error:", e)
        return {
           'success': False,
            'error': str(e)
        }
async def update_bridges(bridge_id, update_fields):
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
    
async def get_version_with_tools(bridge_id, org_id):
    try:
        pipeline = [
            {
                '$match': {'_id': ObjectId(bridge_id), "org_id": org_id}
            },
            {
                '$lookup': {
                    'from': 'apicalls',
                    'localField': 'function_ids', 
                    'foreignField': '_id',
                    'as': 'apiCalls'
                }
            },
            {
                '$addFields': {
                    '_id': {'$toString': '$_id'},
                    'function_ids': {
                        '$map': {
                            'input': '$function_ids',
                            'as': 'fid',
                            'in': {'$toString': '$$fid'}
                        }
                    },
                    'apiCalls': {
                        '$arrayToObject': {
                            '$map': {
                                'input': '$apiCalls',
                                'as': 'api_call',
                                'in': {
                                    'k': {'$toString': '$$api_call._id'},
                                    'v': {
                                        '$mergeObjects': [
                                            '$$api_call',
                                            {
                                                '_id': {'$toString': '$$api_call._id'},
                                                'bridge_ids': {
                                                    '$map': {
                                                        'input': '$$api_call.bridge_ids',
                                                        'as': 'bid',
                                                        'in': {'$toString': '$$bid'}
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
        
        result = list(version_model.aggregate(pipeline))
        
        if not result:
            return {
                'success': False,
                'error': 'No matching records found'
            }
        
        return {
            'success': True,
            'bridges': result[0]
        }
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }
    
async def publish(org_id, version_id):
    try:
        get_version_data = version_model.find_one({'_id': ObjectId(version_id), 'org_id': org_id})
        
        if not get_version_data:
            return {
                "success": False,
                "error": "Version data not found"
            }
        parent_id = str(get_version_data.get('parent_id'))
        if not parent_id:
            return {
                "success": False,
                "error": "Parent ID not found in version data"
            }
        parent_configuration = configurationModel.find_one({'_id': ObjectId(parent_id)})
        
        if not parent_configuration:
            return {
                "success": False,
                "error": "Parent configuration not found"
            }
        published_version_id = str(get_version_data['_id'])
        get_version_data.pop('_id', None)
        updated_configuration = {**parent_configuration, **get_version_data}
        updated_configuration['published_version_id'] = published_version_id
        asyncio.create_task(makeQuestion(parent_id, updated_configuration.get("configuration",{}).get("prompt","")))
        configurationModel.update_one(
            {'_id': ObjectId(parent_id)},
            {'$set': updated_configuration}
        )
        version_model.update_one({'_id': ObjectId(published_version_id)}, {'$set': {'is_drafted': False}})
        
        return {
            "success": True,
            "message": "Configuration updated successfully"
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "success": False,
            "error": str(e)
        }
async def makeQuestion(parent_id, prompt):
    response, headers = await fetch(url='https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion',method='POST',json_body= {"user": prompt,"bridge_id": "67459164ea7147ad4b75f92a"},headers = {'pauthkey': '1b13a7a038ce616635899a239771044c','Content-Type': 'application/json'})
    # Update the document in the configurationModel
    updated_configuration= {"starterQuestion": json.loads(response.get("response",{}).get("data",{}).get("content","{}")).get("questions",[])}
    configurationModel.update_one(
        {'_id': ObjectId(parent_id)},
        {'$set': updated_configuration}
    )