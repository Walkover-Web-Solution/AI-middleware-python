from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
# from src.db_services.ConfigurationServices import get_bridges_by_slug_name_and_name
from src.db_services.ConfigurationServices import create_bridge, get_bridge_by_id, get_all_bridges_in_org,update_bridge, get_bridges, update_tools_calls
from src.configs.modelConfiguration import ModelsConfig as model_configuration
from src.services.utils.helper import Helper
import json
from validations.validation import Bridge_update as bridge_validation
from src.db_services.conversationDbService import storeSystemPrompt


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
        'probablity_cutoff',
        'log_probablity'
        'repetition_penalty',
        'novelty_penalty',
        'n',
        'response_count',
        'additional_stop_sequences',
        'stream',
        'stop',
        'json_mode'
        ]
        model_data = {}
        for key in keys_to_update:
            if key in configurations:
                model_data[key] = configurations[key]['default']
        model_data['type'] = type
        model_data['response_format'] = {
        "type": "default", # need changes
        "cred": {}
        } 
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
        # created_at = bridges.get('created_at') 
        # api_call  = bridges.get('api_call') 
        # api_endpoints = bridges.get('api_endpoints')
        # is_api_call = bridges.get('is_api_call')
        # # responseIds = bridges.get('responseIds')
        # # responseRef = bridges.get('responseRef')
        # # defaultQuestions = bridges.get('defaultQuestions')
        # # actions= bridges.get('actions')

        result = await create_bridge({
            "configuration": configuration,
            "org_id": org_id,
            "name": name,
            "slugName": slugName,
            "service": service,
            "apikey": apikey,
            "bridgeType": bridgeType
        })

        if result.get("success"):
            res = result.get('bridge')
            return res

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)

    except HTTPException as e:
        raise e
    except Exception as error:
        print(f"common error=> {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An unexpected error occurred while creating the bridge. Please try again later.")

async def get_bridge(request, bridge_id: str):
    try:
        org_id = request.state.profile['org']['id']
        bridge = await get_bridge_by_id(org_id, bridge_id)
        return Helper.response_middleware_for_bridge({"succcess": True,"message": "bridge get successfully","bridge":bridge})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)

async def get_all_bridges(request):
    try:
        org_id = request.state.profile['org']['id']
        bridges = await get_all_bridges_in_org(org_id)
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all bridges successfully",
                "bridge" : bridges,
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
        
        if service == 'openai':
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
                    # "gpt-4-0613": restructure_configuration(model_configuration.gpt_4_0613()),
                    # "gpt-4-1106-preview": restructure_configuration(model_configuration.gpt_4_1106_preview()),
                    # "gpt-4-turbo-preview": restructure_configuration(model_configuration.gpt_4_turbo_preview()),
                    # "gpt-4-0125-preview": restructure_configuration(model_configuration.gpt_4_0125_preview()),
                    # "gpt-4-turbo-2024-04-09": restructure_configuration(model_configuration.gpt_4_turbo_2024_04_09()),
                    "gpt-4-turbo": restructure_configuration(model_configuration.gpt_4_turbo()),
                    "gpt-4o": restructure_configuration(model_configuration.gpt_4o()),
                    "gpt-4o-mini": restructure_configuration(model_configuration.gpt_4o_mini()),
                }
                # "embedding": {
                #     "text-embedding-3-large": restructure_configuration(model_configuration.text_embedding_3_large()),
                #     "text-embedding-3-small": restructure_configuration(model_configuration.text_embedding_3_small()),
                #     "text-embedding-ada-002": restructure_configuration(model_configuration.text_embedding_ada_002()),
                # }
            }
        elif service == 'google':
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
        
        elif service == 'anthropic':
            return {
                "chat" : {
                    "claude-3-5-sonnet-20240620" : restructure_configuration(model_configuration.claude_3_5_sonnet_20240620()), 
                    "claude-3-opus-20240229" : restructure_configuration(model_configuration.claude_3_opus_20240229()), 
                    "claude-3-sonnet-20240229" : restructure_configuration(model_configuration.claude_3_sonnet_20240229()), 
                    "claude-3-haiku-20240307" : restructure_configuration(model_configuration.claude_3_haiku_20240307()) 
                }
            }
        
        elif service == 'groq':
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
        service = body.get('service')
        bridgeType = body.get('bridgeType')
        new_configuration = body.get('configuration')
        apikey = body.get('apikey')
        name = body.get('name')
        bridge = await get_bridge_by_id(org_id, bridge_id)
        current_configuration = bridge.get('configuration', {})
        apikey = bridge.get('apikey') if apikey is None else Helper.encrypt(apikey)
        update_fields = {}
        if new_configuration is not None:
            prompt = new_configuration.get('prompt')
            if prompt is not None:
                await storeSystemPrompt(prompt,org_id,bridge_id)
        if slugName is not None:
            update_fields['slugName'] = slugName
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
        result = await update_bridge(bridge_id, update_fields)
        
        if result.get("success"):
            return Helper.response_middleware_for_bridge({
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge" : result.get('result')

            })
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e.json()}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid request body!")


# todo :: change the way tool calls are getting saved in the db
async def get_and_update( bridge_id, org_id, open_api_format, function_name, status="add"):
    try:
        model_config = await get_bridges(bridge_id)
        tools_call = model_config.get('bridges', {}).get('configuration', {}).get('tools', [])

        updated_tools_call = [tool for tool in tools_call if tool['name'] != function_name]

        if status == "add":
            updated_tools_call.append(open_api_format)

        # todo :: add delete from tool call   
        # if status == "delete":
        #     api_endpoints = [item for item in api_endpoints if item != function_name]

        tools_call = updated_tools_call
        configuration = {
            "tools": tools_call
        }

        new_configuration = Helper.update_configuration(model_config['bridges']['configuration'], configuration)
        result = await update_tools_calls(bridge_id, org_id, new_configuration)
        result['tools_call'] = tools_call
        return result

    except Exception as error:
        print(f"error: {error}")
        return {
            "success": False,
            "error": "something went wrong!!"
        }
