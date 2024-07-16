from models.connection import db
from bson import ObjectId
from ..services.commonServices.openAI.openaiCall import chats
import traceback
import json
import os

configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']
staticFlowModel = db['staticFlow']

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

# [done] checked running fine
async def makeStaticData(bridge_id):
    try:
        bridges = configurationModel.find_one({'_id': ObjectId(bridge_id)})

        # Check if bridges exist
        if not bridges:
            return {
                'success': False,
                'error': "bridge id is wrong"
            }
       
        staticCodeData = configurationModel.find_one({'_id': ObjectId(os.getenv('STATIC_FLOW_BRIDGE_ID'))}) #  customer chatbot service 1 // localhost
        
        # Check if userSystemPrompt exists
        if 'configuration' in bridges and 'prompt' in bridges['configuration'] and bridges['configuration']['prompt']:
            userSystemPrompt = bridges['configuration']['prompt'][0]['content']
        else:
            return {
                'success': False,
                'error': "userSystemPrompt not found"
            }
        
        apikey = os.getenv('OPENAI_API_KEY')
        configuration = {}
        configuration['model'] = 'gpt-4o'
        configuration['temperature'] = 0
        configuration['messages'] = [
            {'role': 'system', 'content': staticCodeData['configuration']['prompt'][0]['content']},
            {'role': 'user', 'content': userSystemPrompt}
        ]
        configuration['response_format'] = {'type': 'json_object'}
        openAIResponse = await chats(configuration , apikey)
        try:
            staticCode = json.loads(openAIResponse['modelResponse']['choices'][0]['message']['content'])
            staticCode = staticCode['python_code']
        except json.JSONDecodeError:
            raise('not working correctly')

        if 'staticFlowId' in bridges:
            staticFlowModel.update_one({'_id': bridges['staticFlowId']}, {'$set': {'staticCode': staticCode}})
        else:
            new_static_flow = staticFlowModel.insert_one({'staticCode': staticCode})
            bridges['staticFlowId'] = new_static_flow.inserted_id
            configurationModel.update_one({'_id': ObjectId(bridge_id)}, {'$set': {'staticFlowId': bridges['staticFlowId']}})
        return {
            'success': True,
            'message': "static code added successfully",
        }
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "something went wrong!!"
        }