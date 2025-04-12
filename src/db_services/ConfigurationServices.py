from models.mongo_connection import db
from bson import ObjectId
from ..services.cache_service import find_in_cache, store_in_cache, delete_in_cache
import json

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']
apikeyCredentialsModel = db['apikeycredentials']
version_model = db['configuration_versions']
threadsModel = db['threads']

async def get_bridges(bridge_id = None, org_id = None, version_id = None):
    try:
        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        pipeline = [
            {
                '$match': {'_id': ObjectId(id_to_use), 'org_id': org_id}
            },
            {
                '$project': {
                    'configuration.encoded_prompt': 0
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
                    }
                }
            }
        ]
        
        result = await model.aggregate(pipeline).to_list(length=None)
        bridges = result[0] if result else {}

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
# todo
async def get_bridges_without_tools(bridge_id = None, org_id = None, version_id = None):
    try:
        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        bridge_data = await model.find_one({'_id' : ObjectId(id_to_use)})
        return {
            'success': True,
            'bridges': bridge_data,
        }
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }
    
async def get_bridges_with_tools(bridge_id, org_id, version_id=None):
    try:
        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        pipeline = [
            {
                '$match': {'_id': ObjectId(id_to_use), "org_id": org_id}
            },
            {
                '$project': {
                    'configuration.encoded_prompt': 0
                }
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
        
        result = await model.aggregate(pipeline).to_list(length=None)
        
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

async def get_bridges_with_tools_and_apikeys(bridge_id, org_id, version_id=None):
    try:
        cache_key = f"{version_id or bridge_id}"
        
        # Attempt to retrieve data from Redis cache
        cached_data = await find_in_cache(cache_key)
        if cached_data:
            # Deserialize the cached JSON data
            cached_result = json.loads(cached_data)
            return cached_result  # Return the cached response directly
        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        pipeline = [
            # Stage 0: Match the specific bridge or version with the given org_id
            {
                '$match': {'_id': id_to_use, "org_id": org_id}
            },
            {
                '$project': {
                    'configuration.encoded_prompt': 0
                }
            },
            # Stage 1: Lookup to join with 'apicalls' collection
            {
                '$lookup': {
                    'from': 'apicalls',
                    'localField': 'function_ids', 
                    'foreignField': '_id',
                    'as': 'apiCalls'
                }
            },
            # Stage 2: Restructure fields for _id, function_ids and apiCalls
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
            },
            # Stage 3: Convert 'apikey_object_id' to an array of key-value pairs
            {
                '$addFields': {
                    'apikeys_array': { '$objectToArray': '$apikey_object_id' }
                }
            },
            # Stage 4: Lookup 'apikeycredentials' using the ObjectIds from 'apikeys_array.v'
            {
                '$lookup': {
                    'from': 'apikeycredentials',
                    'let': { 
                        'apikey_ids_object': { 
                            '$map': { 
                                'input': '$apikeys_array.v', 
                                'as': 'id', 
                                'in': {
                                    '$convert': {
                                        'input': '$$id',
                                        'to': 'objectId',
                                        'onError': None,
                                        'onNull': None
                                    }
                                }
                            } 
                        } 
                    },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': { '$in': ['$_id', '$$apikey_ids_object'] }
                            }
                        },
                        {
                            '$project': { 'service': 1, 'apikey': 1 }
                        }
                    ],
                    'as': 'apikeys_docs'
                }
            },
            # Stage 5: Map each service to its corresponding apikey
            {
                '$addFields': {
                    'apikeys': {
                        '$arrayToObject': {
                            '$map': {
                                'input': '$apikeys_array',
                                'as': 'item',
                                'in': [
                                    '$$item.k',  # Service name as the key
                                    {
                                        '$arrayElemAt': [
                                            {
                                                '$map': {
                                                    'input': {
                                                        '$filter': {
                                                            'input': '$apikeys_docs',
                                                            'as': 'doc',
                                                            'cond': { 
                                                                '$eq': [
                                                                    '$$doc._id', 
                                                                    {
                                                                        '$convert': {
                                                                            'input': '$$item.v',
                                                                            'to': 'objectId',
                                                                            'onError': None,
                                                                            'onNull': None
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    },
                                                    'as': 'matched_doc',
                                                    'in': '$$matched_doc.apikey'
                                                }
                                            },
                                            0  # Get the first matched apikey
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            # Stage 6: Lookup 'rag_parent_datas' using 'doc_ids'
            {
                '$lookup': {
                    'from': 'rag_parent_datas',
                    'let': { 
                        'doc_ids': { 
                            '$map': {
                                'input': { '$ifNull': ['$doc_ids', []] },
                                'as': 'doc_id',
                                'in': { '$toObjectId': '$$doc_id' }
                            }
                        }
                    },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': { '$in': ['$_id', '$$doc_ids'] }
                            }
                        },
                        {
                            '$addFields': {
                                '_id': { '$toString': '$_id' }
                            }
                        }
                    ],
                    'as': 'rag_data'
                }
            },
            # Stage 7: (Optional) Remove temporary fields to clean up the output
            {
                '$project': {
                    'apikeys_array': 0,
                    'apikeys_docs': 0,
                    # Exclude additional temporary fields as needed
                }
            }
        ]
        
        # Execute the aggregation pipeline
        result = await model.aggregate(pipeline).to_list(length=None)
        
        if not result:
            return {
                'success': False,
                'error': 'No matching records found'
            }
        
        # Optionally, you can structure the output to include 'apikeys' at the top level
        response =  {
            'success': True,
            'bridges': result[0]
        }
        await store_in_cache(cache_key, response)
        return response
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }



async def update_api_call(id, update_fields):
    try: 
        data = await apiCallModel.find_one_and_update(
                {'_id': ObjectId(id)},
                {'$set': update_fields},
                return_document=True,
                upsert=True
            )
        
        if not data:
            return {
                'success': False,
                'error': 'No records updated or bridge not found'
            }
        if data:
            data['_id'] = str(data['_id'])  # Convert ObjectId to string
            if 'bridge_ids' in data:
                data['bridge_ids'] = [str(bid) for bid in data['bridge_ids']]  # Convert bridge_ids to string
        return {
            'success': True,
            'result': data
        }

    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': 'Something went wrong!'
        }
    

async def update_bridge_ids_in_api_calls(function_id, bridge_id, add=1):
    to_update = {'$set': {'status': 1}}
    if add == 1:
        to_update['$addToSet'] = {'bridge_ids': ObjectId(bridge_id)}
    else:
        to_update['$pull'] = {'bridge_ids': ObjectId(bridge_id)}
                                
    data = await apiCallModel.find_one_and_update(
            {'_id': ObjectId(function_id)},
            to_update,
            return_document=True,
            upsert=True
        )
    if not data:
        return {
            'success': False,
            'error': 'No records updated or bridge not found'
        }
    if data:
        data['_id'] = str(data['_id'])  # Convert ObjectId to string
        if 'bridge_ids' in data:
            data['bridge_ids'] = [str(bid) for bid in data['bridge_ids']]  # Convert bridge_ids to string
    return data

async def get_template_by_id(template_id):
    try:
        template_content = await templateModel.find_one({'_id' : ObjectId(template_id)})
        return template_content
    except Exception as error : 
        print(f"template id error : {error}")
        return None
    
async def create_bridge(data):
    try:
        result = await configurationModel.insert_one(data)
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
    bridge = configurationModel.find({"org_id": org_id}, {
        "_id": 1,
        "name": 1,
        "service": 1,
        "org_id": 1,
        "configuration.model": 1,
        "configuration.prompt": 1,
        "bridgeType": 1,
        "slugName":1,
        "status": 1,
        "versions": 1,
        "published_version_id": 1,
        "total_tokens": 1
    })
    bridges_list = await bridge.to_list(length=None)
    for itr in bridges_list:
        itr['_id'] = str(itr['_id'])
           
    return bridges_list

async def get_bridge_by_id(org_id, bridge_id, version_id=None):
    model = version_model if version_id else configurationModel
    id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
    pipeline = [
        {
            '$match': {'_id': ObjectId(id_to_use), 'org_id': org_id}
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
                }
            }
        }
    ]
    
    result = await model.aggregate(pipeline).to_list(length=None)
    bridge = result[0] if result else None
    return bridge

async def get_bridge_by_slugname(org_id, slug_name):
    try:
        bridge =  await configurationModel.find_one({
            'slugName': slug_name,
            'org_id': org_id
        })

        if bridge and 'responseRef' in bridge:
            response_ref_id = bridge['responseRef']
            response_ref = await configurationModel.find_one({'_id': response_ref_id})
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

async def update_bridge(bridge_id = None, update_fields = None, version_id = None):
    model = version_model if version_id else configurationModel
    id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
    cache_key = f"{version_id if version_id else bridge_id}"
    try:
        updated_bridge = await model.find_one_and_update(
            {'_id': ObjectId(id_to_use)},
            {'$set': update_fields},
            return_document=True,
            upsert=True
        )

        if not updated_bridge:
            raise Exception('No records updated or bridge not found')

        updated_bridge['_id'] = str(updated_bridge['_id'])  # Convert ObjectId to string
        if 'function_ids' in updated_bridge and updated_bridge['function_ids'] is not None:
            updated_bridge['function_ids'] = [str(fid) for fid in updated_bridge['function_ids']]  # Convert function_ids to string

        await delete_in_cache(cache_key)
        return {
            'success': True,
            'result': updated_bridge
        }

    except Exception as error:
        print(error)
        raise  # Re-raise the exception to be handled by the caller

async def update_tools_calls(bridge_id, org_id, configuration):
    try:
        await configurationModel.find_one_and_update(
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
async def get_apikey_creds(id):
    try:
        return await apikeyCredentialsModel.find_one(
            {'_id': ObjectId(id)},
            {'apikey' : 1}
        )
    except Exception as error:
        print(f"error: {error}")
        return {
            'success': False,
            'error': "something went wrong!!"
        }
    
async def update_apikey_creds(version_id):
    try:
        return await apikeyCredentialsModel.update_one(
            {'_id': ObjectId(version_id)},
            {'$set': {'version_ids': [version_id]}}
        )
    except Exception as error:
        print(f"error: {error}")
        return {
            'success': False,
            'error': "something went wrong!!"
        }

async def save_sub_thread_id(org_id, thread_id, sub_thread_id):
    try:
        result = await threadsModel.find_one_and_update(
            {'org_id': org_id, 'sub_thread_id': sub_thread_id},
            {'$setOnInsert': {'thread_id': thread_id}},
            upsert=True,
            return_document=True
        )
        return {
            'success': True,
            'message': f"sub_thread_id saved successfully {result}"
        }
    except Exception as error:
        print(f"error: {error}")
        return {
            'success': False,
            'error': str(error)
        }