from models.mongo_connection import db
from bson import ObjectId
from ..services.cache_service import find_in_cache, store_in_cache, delete_in_cache
import json
from globals import *
from bson import errors
from datetime import datetime

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']
apikeyCredentialsModel = db['apikeycredentials']
version_model = db['configuration_versions']
threadsModel = db['threads']
foldersModel = db['folders']

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
        if not result: 
            raise errors.InvalidId("No matching records found")
        bridges = result[0] if result else {} # Why this line is written
        return {
            'success': True,
            'bridges': bridges,
        }
    except errors.InvalidId as error:
        raise BadRequestException("Invalid Bridge ID provided")
    except Exception as error:
        logger.error(f'Error in get bridges : {str(error)}, {type(error)}')
        return {
            'success': False,
            'error': "something went wrong!!"
        }

async def get_bridges_with_redis(bridge_id = None, org_id = None, version_id = None):
    try:
        cache_key = f"get_{version_id or bridge_id}"
        cached_data = await find_in_cache(cache_key)
        if cached_data:
            cached_result = json.loads(cached_data)
            return cached_result[0] if cached_result else {}
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
        await store_in_cache(cache_key, result)
        return {
            'success': True,
            'bridges': bridges,
        }
    except Exception as error:
        logger.error(f'Error in get bridges : {str(error)}')
        return {
            'success': False,
            'error': "something went wrong!!"
        }
# todo
async def get_bridges_without_tools(bridge_id=None, org_id=None, version_id=None):
    try:
        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        bridge_data = await model.find_one({'_id': ObjectId(id_to_use)})

        if not bridge_data:
            raise errors.InvalidId("No matching bridge found")

        return {
            'success': True,
            'bridges': bridge_data,
        }
    except errors.InvalidId:
        raise BadRequestException("Invalid Bridge ID provided")
    except Exception as error:
        logger.error(f'Error in get_bridges_without_tools : {str(error)}')
        raise error

    
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
            raise errors.InvalidId("No matching bridge found")

        return {
            'success': True,
            'bridges': result[0]
        }
    except errors.InvalidId:
        raise BadRequestException("Invalid Bridge ID provided")
    except Exception as error:
        logger.error(f'Error in get_bridges_with_tools: {str(error)}')
        raise error    

async def get_bridges_with_tools_and_apikeys(bridge_id, org_id, version_id=None):
    try:
        cache_key = f"{version_id or bridge_id}"
       
        # Attempt to retrieve data from Redis cache
        cached_data = await find_in_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)

        model = version_model if version_id else configurationModel
        id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
        pipeline = [
    # Stage 0: Match the specific bridge or version with the given org_id
    {
        '$match': {'_id': ObjectId(id_to_use), "org_id": org_id}
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
    # Stage 3: Convert 'apikey_object_id' to an array of key-value pairs, handling null case
    {
        '$addFields': {
            'apikey_object_id_safe': { '$ifNull': ['$apikey_object_id', {}] },
            'has_apikeys': { '$cond': [{ '$eq': [{ '$type': '$apikey_object_id' }, 'object'] }, True, False] }
        }
    },
    {
        '$addFields': {
            'apikeys_array': { '$cond': [
                '$has_apikeys',
                { '$objectToArray': '$apikey_object_id_safe' },
                []
            ]}
        }
    },
    # Stage 4: Lookup 'apikeycredentials' using the ObjectIds from 'apikeys_array.v'
    {
        '$lookup': {
            'from': 'apikeycredentials',
            'let': {
                'apikey_ids_object': {
                    '$cond': [
                        { '$gt': [{ '$size': '$apikeys_array' }, 0] },
                        {
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
                        },
                        []
                    ]
                }
            },
            'pipeline': [
                {
                    '$match': {
                        '$expr': {
                            '$cond': [
                                { '$gt': [{ '$size': '$$apikey_ids_object' }, 0] },
                                { '$in': ['$_id', '$$apikey_ids_object'] },
                                False
                            ]
                        }
                    }
                },
                {
                    '$project': { 'service': 1, 'apikey': 1 }
                }
            ],
            'as': 'apikeys_docs'
        }
    },
    # Stage 5: Map each service to its corresponding apikey, handling empty case
    {
        '$addFields': {
            'apikeys': {
                '$cond': [
                    { '$gt': [{ '$size': '$apikeys_array' }, 0] },
                    {
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
                    },
                    {}
                ]
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
                        '$expr': { '$or': [{ '$in': ['$_id', '$$doc_ids']}, { '$in': ['$source.nesting.parentDocId', '$$doc_ids']}] }
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
    # Stage 7: Lookup 'pre_tools' data from 'apicalls' collection using the ObjectIds in 'pre_tools'
    {
        '$lookup': {
            'from': 'apicalls',
            'let': {
                'pre_tools_ids': {
                    '$map': {
                        'input': '$pre_tools',
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
                        '$expr': {
                            '$in': ['$_id', {'$ifNull': ['$$pre_tools_ids', []]}]
                        }
                    }
                }
            ],
            'as': 'pre_tools_data'
        }
    },
    # Stage 8: Extract bridge_ids from connected_agents if it exists
    {
        '$addFields': {
            'connected_agents_bridge_ids': {
                '$cond': [
                    { '$and': [
                        { '$ne': ['$connected_agents', None] },
                        { '$ne': ['$connected_agents', {}] },
                        { '$eq': [{ '$type': '$connected_agents' }, 'object'] }
                    ]},
                    {
                        '$map': {
                            'input': { '$objectToArray': '$connected_agents' },
                            'as': 'agent',
                            'in': {
                                '$convert': {
                                    'input': '$$agent.v.bridge_id',
                                    'to': 'objectId',
                                    'onError': None,
                                    'onNull': None
                                }
                            }
                        }
                    },
                    []
                ]
            }
        }
    },
    # Stage 9: Lookup connected_agent_details from configurations collection
    {
        '$lookup': {
            'from': 'configurations',
            'let': {
                'bridge_ids': {
                    '$filter': {
                        'input': '$connected_agents_bridge_ids',
                        'as': 'id',
                        'cond': { '$ne': ['$$id', None] }
                    }
                }
            },
            'pipeline': [
                {
                    '$match': {
                        '$expr': {
                            '$and': [
                                { '$in': ['$_id', '$$bridge_ids'] },
                                { '$ne': ['$connected_agent_details', None] },
                                { '$ne': ['$connected_agent_details', {}] }
                            ]
                        }
                    }
                },
                {
                    '$project': {
                        '_id': 1,
                        'connected_agent_details': 1
                    }
                },
                {
                    '$addFields': {
                        '_id': { '$toString': '$_id' }
                    }
                }
            ],
            'as': 'agent_details_docs'
        }
    },
    # Stage 10: Create connected_agent_details object with bridge_id as key
    {
        '$addFields': {
            'connected_agent_details': {
                '$cond': [
                    { '$gt': [{ '$size': '$agent_details_docs' }, 0] },
                    {
                        '$arrayToObject': {
                            '$map': {
                                'input': '$agent_details_docs',
                                'as': 'doc',
                                'in': [
                                    '$$doc._id',
                                    '$$doc.connected_agent_details'
                                ]
                            }
                        }
                    },
                    {}
                ]
            }
        }
    },
    # Stage 11: Remove temporary fields to clean up the output
    {
        '$project': {
            'apikeys_array': 0,
            'apikeys_docs': 0,
            'apikey_object_id_safe': 0,
            'has_apikeys': 0,
            'connected_agents_bridge_ids': 0,
            'agent_details_docs': 0
            # Exclude additional temporary fields as needed
        }
    }
]
       
        # Execute the main aggregation pipeline
        result = await model.aggregate(pipeline).to_list(length=None)
       
        if not result:
            return {
                'success': False,
                'error': 'No matching records found'
            }
        
        bridge_data = result[0]
        
        # Check if folder_id is present and fetch folder API keys
        if bridge_data.get('folder_id'):
            
            folder_pipeline = [
                # Stage 1: Match the folder document
                {
                    '$match': {'_id': ObjectId(bridge_data['folder_id'])}
                },
                # Stage 2: Convert apikey_object_id to array format
                {
                    '$addFields': {
                        'apikey_object_id_safe': { '$ifNull': ['$apikey_object_id', {}] },
                        'has_apikeys': { '$cond': [{ '$eq': [{ '$type': '$apikey_object_id' }, 'object'] }, True, False] }
                    }
                },
                {
                    '$addFields': {
                        'apikeys_array': { '$cond': [
                            '$has_apikeys',
                            { '$objectToArray': '$apikey_object_id_safe' },
                            []
                        ]}
                    }
                },
                # Stage 3: Lookup apikeycredentials
                {
                    '$lookup': {
                        'from': 'apikeycredentials',
                        'let': {
                            'apikey_ids_object': {
                                '$cond': [
                                    { '$gt': [{ '$size': '$apikeys_array' }, 0] },
                                    {
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
                                    },
                                    []
                                ]
                            }
                        },
                        'pipeline': [
                            {
                                '$match': {
                                    '$expr': {
                                        '$in': ['$_id', { '$ifNull': ['$$apikey_ids_object', []] }]
                                    }
                                }
                            }
                        ],
                        'as': 'apikeys_docs'
                    }
                },
                # Stage 4: Create folder_apikeys object
                {
                    '$addFields': {
                        'folder_apikeys': {
                            '$cond': [
                                { '$gt': [{ '$size': '$apikeys_array' }, 0] },
                                {
                                    '$arrayToObject': {
                                        '$map': {
                                            'input': '$apikeys_array',
                                            'as': 'item',
                                            'in': {
                                                'k': '$$item.k',
                                                'v': {
                                                    '$arrayElemAt': [
                                                        {
                                                            '$map': {
                                                                'input': {
                                                                    '$filter': {
                                                                        'input': '$apikeys_docs',
                                                                        'cond': {
                                                                            '$eq': [
                                                                                '$$this._id',
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
                                                        0
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                },
                                {}
                            ]
                        }
                    }
                },
                # Stage 5: Project only folder_apikeys
                {
                    '$project': {
                        'folder_apikeys': 1
                    }
                }
            ]
            
            # Execute folder pipeline on folders collection
            folder_result = await foldersModel.aggregate(folder_pipeline).to_list(length=None)
            
            # Append folder_apikeys to bridge_data if found
            if folder_result and folder_result[0].get('folder_apikeys'):
                bridge_data['folder_apikeys'] = folder_result[0]['folder_apikeys']
            else:
                bridge_data['folder_apikeys'] = {}
        else:
            # No folder_id, set empty folder_apikeys
            bridge_data['folder_apikeys'] = {}
       
        # Structure the final response
        response = {
            'success': True,
            'bridges': bridge_data
        }
        await store_in_cache(cache_key, response)
        return response

    except errors.InvalidId:
        raise BadRequestException("Invalid Bridge ID provided")
    except Exception as error:
        logger.error(f'Error in get_bridges_with_tools_and_apikeys: {str(error)}')
        raise error



    

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

async def update_built_in_tools(version_id, tool, add=1):
    to_update = {'$set': {'status': 1}}
    if add == 1:
        to_update['$addToSet'] = {'built_in_tools': tool}
    else:
        to_update['$pull'] = {'built_in_tools': tool}
    
    data = await version_model.find_one_and_update(
        {'_id': ObjectId(version_id)},
        to_update,
        return_document=True,
        upsert=True
    )
    
    if not data:
        return {
            'success': False,
            'error': 'No records updated or version not found'
        }
    
    if 'built_in_tools' not in data:
        data['built_in_tools'] = []
    
    return data

async def update_agents(version_id, agents, add=1):
    if add == 1:
        # Add or update the connected agents
        to_update = {'$set': {f'connected_agents.{agent_name}': agent_info for agent_name, agent_info in agents.items()}}
    else:
        # Remove the specified connected agents
        to_update = {'$unset': {f'connected_agents.{agent_name}': "" for agent_name in agents.keys()}}
   
    data = await version_model.find_one_and_update(
        {'_id': ObjectId(version_id)},
        to_update,
        return_document=True,
        upsert=True
    )
   
    if not data:
        raise 'No records updated or version not found'
   
    if 'connected_agents' not in data:
        data['connected_agents'] = {}
   
    return data

async def update_agents(version_id, agents, add=1):
    if add == 1:
        # Add or update the connected agents
        to_update = {'$set': {f'connected_agents.{agent_name}': agent_info for agent_name, agent_info in agents.items()}}
    else:
        # Remove the specified connected agents
        to_update = {'$unset': {f'connected_agents.{agent_name}': "" for agent_name in agents.keys()}}
    
    data = await version_model.find_one_and_update(
        {'_id': ObjectId(version_id)},
        to_update,
        return_document=True,
        upsert=True
    )
    
    if not data:
        return {
            'success': False,
            'error': 'No records updated or version not found'
        }
    
    if 'connected_agents' not in data:
        data['connected_agents'] = {}
    
    return data

async def get_template_by_id(template_id):
    try:
        cache_key = f"template_{template_id}"
        template_content = await find_in_cache(cache_key)
        if template_content:
            template_content = json.loads(template_content)
            return template_content
        
        template_content = await templateModel.find_one({'_id' : ObjectId(template_id)})
        await store_in_cache(cache_key, template_content)
        return template_content
    except Exception as error : 
        logger.error(f"Error in get_template_by_id: {str(error)}")
        return None
    
async def create_bridge(data):
    try:
        result = await configurationModel.insert_one(data)
        return {
            'success': True,
            'bridge': {**data, '_id': str(result.inserted_id)}
        }
    except Exception as error:
        logger.error(f"Error in create_bridge: {str(error)}")
        raise BadRequestException("Failed to create bridge")

async def get_all_bridges_in_org(org_id, folder_id, user_id, isEmbedUser):
    query = {"org_id": org_id}
    query["folder_id"] = folder_id or None
    if user_id and isEmbedUser:
        query["user_id"] = user_id
    bridge = configurationModel.find(query, {
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
        "total_tokens": 1,
        "variables_state" : 1,
        "agent_variables" : 1,
        "bridge_status":1,
        "versions":1,
        'connected_agents':1,
        'function_ids':1,
        'connected_agent_details':1,
        'bridge_summary': 1 
    })
    bridges_list = await bridge.to_list(length=None)
    for itr in bridges_list:
        itr["_id"] = str(itr["_id"])
        if "function_ids" in itr and itr["function_ids"]:
            # Convert every ObjectId in the list to a string
            itr["function_ids"] = [str(fid) for fid in itr["function_ids"]]
    return bridges_list

async def get_all_bridges_in_org_by_org_id(org_id):
    query = {"org_id": org_id}
    bridge_cursor = configurationModel.find(query, {
        "_id": 1,
        "name": 1,
        "slugName":1,
    })
    bridges_list = await bridge_cursor.to_list(length=None)
    for bridge in bridges_list:
        bridge['_id'] = str(bridge['_id'])
            
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

        if not bridge:
            raise BadRequestException("Bridge not found")

        if 'responseRef' in bridge:
            response_ref_id = bridge['responseRef']
            response_ref = await configurationModel.find_one({'_id': response_ref_id})
            bridge['responseRef'] = response_ref

        return bridge
    except BadRequestException:
        raise
    except Exception as error:
        logger.error(f'Error in get_bridge_by_slugname: {str(error)}')
        raise BadRequestException("Failed to fetch bridge by slugName")


async def update_bridge(bridge_id = None, update_fields = None, version_id = None):
    model = version_model if version_id else configurationModel
    id_to_use = ObjectId(version_id) if version_id else ObjectId(bridge_id)
    cache_key = f"{version_id if version_id else bridge_id}"
    
    updated_bridge = await model.find_one_and_update(
        {'_id': ObjectId(id_to_use)},
        {'$set': update_fields},
        return_document=True,
        upsert=True
    )

    if not updated_bridge:
        raise BadRequestException('Bridge not found or no records updated')

    updated_bridge['_id'] = str(updated_bridge['_id'])  # Convert ObjectId to string
    if 'function_ids' in updated_bridge and updated_bridge['function_ids'] is not None:
        updated_bridge['function_ids'] = [str(fid) for fid in updated_bridge['function_ids']]  # Convert function_ids to string

    await delete_in_cache(cache_key)
    return {
        'success': True,
        'result': updated_bridge
    }


async def get_apikey_creds(org_id, apikey_object_ids):
    for service, object_id in apikey_object_ids.items():
        apikey_cred = await apikeyCredentialsModel.find_one(
            {'_id': ObjectId(object_id), 'org_id': org_id},
            {'apikey': 1}
        )
        if not apikey_cred:
            raise BadRequestException(f"Apikey for {service} not found")
    
async def update_apikey_creds(version_id, apikey_object_ids):
    try:
        if isinstance(apikey_object_ids, dict):
            # First, remove the version_id from any apikeycredentials documents that contain it
            await apikeyCredentialsModel.update_many(
                {'version_ids': version_id},
                {'$pull': {'version_ids': version_id}}
            )
            
            for service, api_key_id in apikey_object_ids.items():
                # Then add the version_id to the target document
                await apikeyCredentialsModel.update_one(
                    {'_id': ObjectId(api_key_id)},
                    {'$addToSet': {'version_ids': version_id}},
                    upsert=True
                )
        return True
    except Exception as error:
        logger.error(f"Error in update_apikey_creds: {str(error)}")
        raise error

async def save_sub_thread_id(org_id, thread_id, sub_thread_id, display_name, bridge_id): # bridge_id is now a required parameter
    try:
        update_data = {'$setOnInsert': {'thread_id': thread_id}}
        
        # Fields to be set or updated
        set_fields = {'bridge_id': bridge_id} # bridge_id will always be set
        if display_name is not None and isinstance(display_name, str):
            set_fields['display_name'] = display_name
            
        update_data['$set'] = set_fields
       
        result = await threadsModel.find_one_and_update(
            {'org_id': org_id,'thread_id': thread_id, 'sub_thread_id': sub_thread_id, 'bridge_id': bridge_id},
            update_data,
            upsert=True,
            return_document=True
        )
        return {
            'success': True,
            'message': f"sub_thread_id and bridge_id saved successfully {result}" # Updated success message
        }
    except Exception as error:
        logger.error(f"Error in save_sub_thread_id: {error}")
        raise error    

async def get_all_agents_data(user_email):
    query = {
        "$or": [
            {"page_config.availability": "public"},
            {
                "page_config.availability": "private",
                "page_config.allowedUsers": user_email
            }
        ]
    }
    cursor = configurationModel.find(query)
    data = [doc async for doc in cursor]
    
    return data


async def get_agents_data(slug_name, user_email):
    bridges = await configurationModel.find_one({
        "$or": [
            {
                "$and": [
                    {"page_config.availability": "public"},
                    {"page_config.url_slugname": slug_name}
                ]
            },
            {
                "$and": [
                    {"page_config.availability": "private"},
                    {"page_config.url_slugname": slug_name},
                    {"page_config.allowedUsers": user_email}
                ]
            }
        ]
    })
    return bridges

async def get_bridges_and_versions_by_model(model_name):
    try:
        cursor = configurationModel.find(
            {"configuration.model": model_name},
            {"org_id": 1, "name": 1, "_id": 1,"versions":1}  # projection
        )
        bridges = await cursor.to_list(length=None)
        bridges = [
            {**{k: v for k, v in bridge.items() if k != "_id"}, "bridge_id": str(bridge["_id"])}
            for bridge in bridges
        ]
        return bridges
    except Exception as error:
        logger.error(f'Error in get_bridges_and_versions_by_model: {str(error)}')
        raise error

async def update_apikey_last_used(org_id, service, apikey_object_id):
    try:
        object_id = apikey_object_id[service]
            
        if not object_id:
            logger.warning(f"No API key object ID found for service: {service}")
            return
            
        # Update the lastUsed field
        result = await apikeyCredentialsModel.update_one(
            {'_id': ObjectId(object_id), 'org_id': org_id},
            {'$set': {'lastused': datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated lastused for API key {object_id} in service {service}")
        else:
            logger.warning(f"API key {object_id} not found or not updated for service {service}")
            
    except Exception as error:
        logger.error(f'Error updating API key lastused: {str(error)}')