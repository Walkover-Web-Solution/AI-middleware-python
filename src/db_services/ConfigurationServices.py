from models.mongo_connection import db
from bson import ObjectId
import traceback

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']
apikeyCredentialsModel = db['apikeycredentials']
version_model = db['configuration_versions']

async def get_bridges(bridge_id = None, org_id = None, version_id = None):
    try:
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
    try: 
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

async def get_api_call_by_names(names, org_id):
    try:
        if not isinstance(names, list):
            names = [names]
        pipeline = [
    {
        '$match': {
            '$or': [
                {'function_name': {'$in': names}},
                {'endpoint': {'$in': names}}
            ],
            'org_id': org_id
        }
    },
    {
        '$addFields': {
            'name': {
                '$cond': {
                    'if': {'$ifNull': ['$function_name', False]},
                    'then': '$function_name',
                    'else': '$endpoint'
                }
            },
            'code': {
                '$cond': {
                    'if': {'$ifNull': ['$code', False]},
                    'then': '$code',
                    'else': '$axios'
                }
            }
        }
    },
    {
        '$project': {
            '_id': 0,  # Exclude the `_id` from the response if not needed
            'name': 1,
            'code': 1,
            'is_python': 1
        }
    },
    {
        '$group': {
            '_id': None,  # We don't need an actual group key
            'apiCalls': {
                '$push': {
                    'name': '$name',
                    'code': '$code',
                    'is_python': '$is_python'
                }
            }
        }
    },
    {
        '$project': {
            '_id': 0,  # Exclude the group _id
            'apiCalls': {
                '$arrayToObject': {
                    '$map': {
                        'input': '$apiCalls',
                        'as': 'api',
                        'in': {
                            'k': '$$api.name',  # Use the name as the key
                            'v': {
                                'code': '$$api.code',
                                'is_python': '$$api.is_python',
                                'name': '$$api.name'
                            }
                        }
                    }
                }
            }
        }
    }
]
        return await apiCallModel.aggregate(pipeline).to_list(length=None)

    except Exception as error:
        print(f"error: {error}")
        raise error

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
        "published_version_id": 1
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
    try:
        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        updated_bridge = await model.find_one_and_update(
            {'_id': ObjectId(id_to_use)},
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
            if 'function_ids' in updated_bridge and updated_bridge['function_ids'] is not None:
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