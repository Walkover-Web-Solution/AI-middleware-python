from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.db_services.ConfigurationServices import create_bridge, get_bridge_by_id, get_all_bridges_in_org, update_bridge, update_bridge_ids_in_api_calls, get_bridges_with_tools, get_apikey_creds
from src.configs.modelConfiguration import ModelsConfig as model_configuration
from src.services.utils.helper import Helper
import json
from config import Config
from ..configs.constant import service_name
from src.db_services.conversationDbService import storeSystemPrompt
from bson import ObjectId
from datetime import datetime, timezone

async def create_bridges_controller(request):
    try:
        bridges = await request.json()
        type = bridges.get('type')
        org_id = request.state.profile['org']['id']
        service = bridges.get('service')
        model = bridges.get('model')
        name = bridges.get('name')
        slugName = bridges.get('slugName')
        bridgeType = bridges.get('bridgeType')
        modelname = model.replace("-", "_").replace(".", "_")
        configuration = getattr(model_configuration,modelname,None)
        configurations = configuration()['configuration']
        keys_to_update = [
        'model',
        'creativity_level',
        'max_tokens',
        'probability_cutoff',
        'log_probablity',
        'repetition_penalty',
        'novelty_penalty',
        'n',
        'response_count',
        'additional_stop_sequences',
        'stream',
        'stop',
        'response_type',
        'tool_choice',
        ]
        model_data = {}
        for key in keys_to_update:
            if key in configurations:
                model_data[key] = configurations[key]['default'] if key == 'model' else 'default'
        model_data['type'] = type
        model_data['response_format'] = {
        "type": "default", # need changes
        "cred": {}
        } 
        model_data["is_rich_text"]= True
        result = await create_bridge({
            "configuration": model_data,
            "name": name,
            "slugName": slugName,
            "service": service,
            "bridgeType": bridgeType,
            "org_id" : org_id
        })
        if result.get("success"):
            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Bridge created successfully",
                "bridge" : json.loads(json.dumps(result.get('bridge'), default=str))

            })
        else:
            return JSONResponse(status_code=400, content={
                "success": False,
                "message": json.loads(json.dumps(result.get('error'), default=str))
            })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)    

async def duplicate_create_bridges(bridges):
    try:

        org_id = bridges.get('org_id')
        service = bridges.get('service') 
        bridgeType = bridges.get('bridgeType')
        name = bridges.get('name')
        configuration = bridges.get('configuration') 
        apikey = bridges.get('apikey') 
        slugName = bridges.get('slugName') 
        function_ids = []
        if bridges.get('function_ids'):
            function_ids = [ObjectId(fid) for fid in bridges.get('function_ids')]
        actions= bridges.get('actions', {})
        apikey_object_id = bridges.get('apikey_object_id')

        result = await create_bridge({
            "configuration": configuration,
            "org_id": org_id,
            "name": name,
            "slugName": slugName,
            "service": service,
            "apikey": apikey,
            "bridgeType": bridgeType,
            "function_ids":function_ids,
            "actions": actions,
            "apikey_object_id":apikey_object_id
        })

        if result.get("success"):
            res = result.get('bridge')
            # todo: optimize in future
            if(function_ids):
                for function_id in function_ids:
                    await update_bridge_ids_in_api_calls(function_id, str(res.get("_id")), 1)
            return res

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)

    except HTTPException as e:
        raise e
    except Exception as error:
        print(f"common error=> {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An unexpected error occurred while creating the bridge. Please try again later.")

async def get_bridge(request, bridge_id: str):
    try:
        bridge = await get_bridges_with_tools(bridge_id,request.state.profile['org']['id'])
        prompt = bridge.get('bridges').get('configuration',{}).get('prompt')
        variables = []
        if prompt is not None:
            variables = Helper.find_variables_in_string(prompt)
        variables_path = bridge.get('bridges').get('variables_path',{})
        path_variables = []
        for script_id, vars_dict in variables_path.items():
            path_variables.extend(vars_dict.keys())
        all_variables = variables + path_variables
        bridge.get('bridges')['all_varaibles'] = all_variables
        return Helper.response_middleware_for_bridge({"succcess": True,"message": "bridge get successfully","bridge":bridge.get("bridges", {})})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)

async def get_all_bridges(request):
    try:
        org_id = request.state.profile['org']['id']
        bridges = await get_all_bridges_in_org(org_id)
        embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.PROJECT_ID, "user_id": org_id },Config.Access_key )
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all bridges successfully",
                "bridge" : bridges,
                "embed_token": embed_token,
                "org_id": org_id

            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
async def get_all_service_models_controller(service):
    try:
        service = service.lower()
        def restructure_configuration(config):
            model_field = config.get("configuration", {}).get("model", "")
            additional_parameters = config.get("configuration", {})
            outputConfig = config.get("outputConfig", {})
            
            return {
                "configuration": {
                    "model": model_field,
                    "additional_parameters": additional_parameters,
                    "outputConfig": outputConfig
                }
            }
        
        if service == service_name['openai']:
            return {
                # "completion": {
                #     "gpt_3_5_turbo_instruct": restructure_configuration(model_configuration.gpt_3_5_turbo_instruct())
                # },
                "chat": {
                    "gpt-3.5-turbo": restructure_configuration(model_configuration.gpt_3_5_turbo()),
                    # "gpt-3.5-turbo-0613": restructure_configuration(model_configuration.gpt_3_5_turbo_0613()),
                    # "gpt-3.5-turbo-0125": restructure_configuration(model_configuration.gpt_3_5_turbo_0125()),
                    # "gpt-3.5-turbo_0301": restructure_configuration(model_configuration.gpt_3_5_turbo_0301()),
                    # "gpt-3.5-turbo-1106": restructure_configuration(model_configuration.gpt_3_5_turbo_1106()),
                    # "gpt-3.5-turbo-16k": restructure_configuration(model_configuration.gpt_3_5_turbo_16k()),
                    # "gpt-3.5-turbo-16k-0613": restructure_configuration(model_configuration.gpt_3_5_turbo_16k_0613()),
                    "gpt-4": restructure_configuration(model_configuration.gpt_4()),
                    # "gpt-4-1106-preview": restructure_configuration(model_configuration.gpt_4_1106_preview()),
                    # "gpt-4-turbo-preview": restructure_configuration(model_configuration.gpt_4_turbo_preview()),
                    # "gpt-4-0125-preview": restructure_configuration(model_configuration.gpt_4_0125_preview()),
                    # "gpt-4-turbo-2024-04-09": restructure_configuration(model_configuration.gpt_4_turbo_2024_04_09()),
                    "gpt-4-turbo": restructure_configuration(model_configuration.gpt_4_turbo()),
                    "gpt-4o": restructure_configuration(model_configuration.gpt_4o()),
                    "chatgpt-4o-latest": restructure_configuration(model_configuration.chatgpt_4o_latest()),
                    "gpt-4o-mini": restructure_configuration(model_configuration.gpt_4o_mini()),
                },
                "fine-tune" : {
                     "gpt-4-0613": restructure_configuration(model_configuration.gpt_4_0613()),
                     "gpt-4o-2024-08-06": restructure_configuration(model_configuration.gpt_4o_2024_08_06()),
                     "gpt-4o-mini-2024-07-18": restructure_configuration(model_configuration.gpt_4o_mini_2024_07_18()),

                }
                # "embedding": {
                #     "text-embedding-3-large": restructure_configuration(model_configuration.text_embedding_3_large()),
                #     "text-embedding-3-small": restructure_configuration(model_configuration.text_embedding_3_small()),
                #     "text-embedding-ada-002": restructure_configuration(model_configuration.text_embedding_ada_002()),
                # }
            }
        elif service == service_name['gemini']:
            return {
                # "completion": {
                #     "gemini-1.5-pro": restructure_configuration(model_configuration.gemini_1_5_pro()),
                #     "gemini-pro": restructure_configuration(model_configuration.gemini_pro()),
                #     "gemini-1.5-Flash": restructure_configuration(model_configuration.gemini_1_5_Flash()),
                #     "gemini-1.0-pro": restructure_configuration(model_configuration.gemini_1_0_pro()),
                #     "gemini-1.0-pro-vision": restructure_configuration(model_configuration.gemini_1_0_pro_vision())
                # },
                "chat": {
                    "gemini-1.5-pro": restructure_configuration(model_configuration.gemini_1_5_pro()),
                    "gemini-pro": restructure_configuration(model_configuration.gemini_pro()),
                    "gemini-1.5-Flash": restructure_configuration(model_configuration.gemini_1_5_Flash()),
                    "gemini-1.0-pro": restructure_configuration(model_configuration.gemini_1_0_pro()),
                    "gemini-1.0-pro-vision": restructure_configuration(model_configuration.gemini_1_0_pro_vision())
                }
            }
        
        elif service == service_name['anthropic']:
            return {
                "chat" : {
                    "claude-3-5-sonnet-20240620" : restructure_configuration(model_configuration.claude_3_5_sonnet_20240620()), 
                    "claude-3-opus-20240229" : restructure_configuration(model_configuration.claude_3_opus_20240229()), 
                    "claude-3-sonnet-20240229" : restructure_configuration(model_configuration.claude_3_sonnet_20240229()), 
                    "claude-3-haiku-20240307" : restructure_configuration(model_configuration.claude_3_haiku_20240307()) 
                }
            }
        
        elif service == service_name['groq']:
            return {
                "chat" : {
                    "llama-3.1-405b-reasoning" : restructure_configuration(model_configuration.llama_3_1_405b_reasoning()),
                    "llama-3.1-70b-versatile" : restructure_configuration(model_configuration.llama_3_1_70b_versatile()),
                    "llama-3.1-8b-instant" : restructure_configuration(model_configuration.llama_3_1_8b_instant()),
                    "llama3-groq-70b-8192-tool-use-preview" : restructure_configuration(model_configuration.llama3_groq_70b_8192_tool_use_preview()),
                    "llama3-groq-8b-8192-tool-use-preview" : restructure_configuration(model_configuration.llama3_groq_8b_8192_tool_use_preview()),
                    "llama3-70b-8192" : restructure_configuration(model_configuration.llama3_70b_8192()),
                    "llama3-8b-8192" : restructure_configuration(model_configuration.llama3_8b_8192()),
                    "mixtral-8x7b-32768" : restructure_configuration(model_configuration.mixtral_8x7b_32768()),
                    "gemma-7b-it" : restructure_configuration(model_configuration.gemma_7b_it()),
                    "gemma2-9b-it" : restructure_configuration(model_configuration.gemma2_9b_it())
                }
            }


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_bridge_controller(request,bridge_id):
    try:
        body  = await request.json()
        org_id = request.state.profile['org']['id']
        slugName = body.get('slugName')
        user_reference=body.get('user_reference')
        service = body.get('service')
        bridgeType = body.get('bridgeType')
        new_configuration = body.get('configuration')
        apikey = body.get('apikey')
        apikey_object_id = body.get('apikey_object_id')
        variables_path = body.get('variables_path')
        user_id = request.state.profile['user']['id']
        update_fields = {}
        user_history = []
        if apikey_object_id is not None:
            update_fields['apikey_object_id'] = apikey_object_id
            data = await get_apikey_creds(apikey_object_id)
            apikey = data.get('apikey',"")
        name = body.get('name')
        function_id = body.get('functionData', {}).get('function_id', None)
        function_operation = body.get('functionData', {}).get('function_operation')
        function_name = body.get('functionData', {}).get('function_name',None)
        bridge = await get_bridge_by_id(org_id, bridge_id)
        if new_configuration and 'type' in new_configuration and new_configuration.get('type') != 'fine-tune':
            new_configuration['fine_tune_model'] = {}
            new_configuration['fine_tune_model']['current_model'] = None
        current_configuration = bridge.get('configuration', {})
        current_variables_path = bridge.get('variables_path',{})
        function_ids = bridge.get('function_ids') or []
        prompt = new_configuration.get('prompt') if new_configuration else None
        if prompt:
            result = await storeSystemPrompt(prompt, org_id, bridge_id)
            new_configuration['system_prompt_version_id'] = result.get('id')
        if slugName is not None:
            update_fields['slugName'] = slugName
        if user_reference is not None:
            update_fields['user_reference'] = user_reference
        if service is not None:
            update_fields['service'] = service
        if bridgeType is not None:
            update_fields['bridgeType'] = bridgeType
        if new_configuration is not None:
            updated_configuration = {**current_configuration, **new_configuration}
            update_fields['configuration'] = updated_configuration
        if apikey is not None:
            update_fields['apikey'] = apikey
        if name is not None:
            update_fields['name'] = name
        if variables_path is not None:
            updated_variables_path = {**current_variables_path, **variables_path}
            for key, value in updated_variables_path.items():
                if isinstance(value, list):
                    updated_variables_path[key] = {}
            update_fields['variables_path'] = updated_variables_path
        if function_id is not None: 
                if function_operation is not None:      # to add function id 
                    if function_id not in function_ids:
                        function_ids.append(function_id)
                        update_fields['function_ids'] = [ObjectId(fid) for fid in function_ids]
                        await update_bridge_ids_in_api_calls(function_id, bridge_id, 1)
                elif function_operation is None:        # to remove function id 
                    if function_name is not None:   
                         if function_name in  current_variables_path:
                             del current_variables_path[function_name]
                             update_fields['variables_path'] = current_variables_path
                    if function_id in function_ids:
                        function_ids.remove(function_id)
                        update_fields['function_ids'] = [ObjectId(fid) for fid in function_ids]
                        await update_bridge_ids_in_api_calls(function_id, bridge_id, 0)
        
        for key, value in body.items():
            if key == 'configuration':
                for configuration in value.keys():
                    user_history.append({
                        'type': configuration,
                        'user_id': user_id,
                        'time': datetime.now(timezone.utc).isoformat()
                    })
            else:
                user_history.append({
                    'type': key,
                    'user_id': user_id,
                    'time': datetime.now(timezone.utc).isoformat()
                })

        existing_history = bridge.get('user_history', [])
        existing_history.extend(user_history)
        if len(existing_history) > 20:
            existing_history = existing_history[-20:]  
        update_fields['user_history'] = existing_history

        await update_bridge(bridge_id, update_fields) # todo :: add transaction
        result = await get_bridges_with_tools(bridge_id, org_id)
        
        if result.get("success"):
            return Helper.response_middleware_for_bridge({
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge" : result.get('bridges')

            })
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e.json()}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid request body!")