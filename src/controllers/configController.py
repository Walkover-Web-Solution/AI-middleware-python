from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.db_services.ConfigurationServices import create_bridge, get_all_bridges_in_org_by_org_id, get_bridge_by_id, get_all_bridges_in_org, update_bridge, update_bridge_ids_in_api_calls, get_bridges_with_tools, get_apikey_creds, update_apikey_creds, update_built_in_tools, update_agents, get_all_agents_data, get_agents_data, get_bridges_and_versions_by_model
from src.configs.modelConfiguration import ModelsConfig as model_configuration
from src.services.utils.helper import Helper
import json
from config import Config
from ..configs.constant import redis_keys, service_name
from src.db_services.conversationDbService import storeSystemPrompt, add_bulk_user_entries
from bson import ObjectId
from src.services.utils.getDefaultValue import get_default_values_controller
from src.db_services.bridge_version_services import create_bridge_version
from src.services.utils.apicallUtills import delete_all_version_and_bridge_ids_from_cache
from src.configs.model_configuration import model_config_document
from globals import *
from src.configs.constant import bridge_ids
from src.services.utils.ai_call_util import call_ai_middleware
from src.services.cache_service import find_in_cache
from src.db_services.templateDbservice import get_template

async def create_bridges_controller(request):
    try:
        bridges = await request.json()
        purpose = bridges.get('purpose')
        org_id = request.state.profile['org']['id']
        folder_id = request.state.folder_id if hasattr(request.state, 'folder_id') else None
        user_id = request.state.user_id
        isEmbedUser = request.state.embed
        all_bridge = await get_all_bridges_in_org_by_org_id(org_id)
        prompt = None
        if 'templateId' in bridges:
            template_id = bridges['templateId']
            template_data = await get_template(template_id)
            if not template_data:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "Template not found"}
                )
            # Override prompt with template's prompt if available
            prompt = template_data.get('prompt', prompt)
        
        if purpose is not None:
            variables = {
                "purpose": purpose,
                 "all_bridge_names": [bridge.get("name") for bridge in all_bridge]
            }
            user = "Generate Bridge Configuration accroding to the given user purpose."
            bridge_data =  await call_ai_middleware(user, bridge_id = bridge_ids['create_bridge_using_ai'], variables = variables)
            model = bridge_data.get('model')
            service = bridge_data.get('service')
            name = bridge_data.get('name')
            prompt = bridge_data.get('system_prompt')
            slugName = bridge_data.get('name')
            type = bridge_data.get('type')

        else:
            name_next_count = 1
            slug_next_count = 1
            if bridges.get('name').startswith("untitled_agent_"):
                if all_bridge:
                    for bridge in all_bridge:
                        if bridge.get('name') and bridge.get('name').startswith("untitled_agent_"):
                            num = int(bridge.get('name').replace("untitled_agent_", ""))
                            if num > name_next_count:
                                name_next_count = num
                        if bridge.get('slugName') and bridge.get('slugName').startswith("untitled_agent_"):
                            num = int(bridge.get('slugName').replace("untitled_agent_", ""))
                            if num > slug_next_count:
                                slug_next_count = num
                    name_next_count = name_next_count + 1
                    slug_next_count = slug_next_count + 1
            service = bridges.get('service')
            model = bridges.get('model')
            name = bridges.get('name') if not bridges.get('name').startswith("untitled_agent_") else f"untitled_agent_{name_next_count}"
            type = bridges.get('type')
            slugName = bridges.get('slugName') if not bridges.get('slugName').startswith("untitled_agent_") else f"untitled_agent_{slug_next_count}"
        bridgeType = bridges.get('bridgeType')
        modelObj = model_config_document[service][model]
        configurations = modelObj['configuration']
        status = 1
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
        'size',
        'quality',
        'style',
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
        model_data["is_rich_text"]= False
        # Add default fallback configuration
        fall_back = {
            "is_enable": True,
            "service": "ai_ml",
            "model": "gpt-oss-120b"
        }
        if prompt is not None:
            model_data['prompt'] = prompt
        result = await create_bridge({
            "configuration": model_data,
            "name": name,
            "slugName": slugName,
            "service": service,
            "bridgeType": bridgeType,
            "org_id" : org_id,
            "status": status,
            "gpt_memory" : True,
            "folder_id" : folder_id,
            "user_id" : user_id,
            "fall_back" : fall_back
        })
        create_version = await create_bridge_version(result['bridge'])
        update_fields = {'versions' : [create_version]}
        updated_bridge_result = (await update_bridge(str(result['bridge']['_id']), update_fields)).get('result',{})
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Bridge created successfully",
            "bridge" : json.loads(json.dumps(updated_bridge_result, default=str))
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail= "Error in creating bridge: "+ str(e))   
     
async def create_bridges_using_ai_controller(request):
    try:
        body = await request.json()
        purpose = body.get('purpose')
        bridge_type = body.get('bridgeType')
        result = []
        proxy_auth_token = request.headers.get("proxy_auth_token")
        variables = {"proxy_auth_token": proxy_auth_token, "purpose": purpose, "bridgeType": bridge_type}
        bridge = await call_ai_middleware(purpose, bridge_id = bridge_ids['create_bridge_using_ai'], variables = variables)
        if bridge:
            return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Bridge created successfully",
                "bridge" : bridge['bridge']
            })
        else:
            return JSONResponse(status_code=400, content={
                "success": False,
                "message": json.loads(json.dumps(result[0].get('error'), default=str))
            })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)    


async def get_bridge(request, bridge_id: str):
    try:
        bridge = await get_bridges_with_tools(bridge_id,request.state.profile['org']['id'])
        if(bridge.get('bridges') is None):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bridge not found")
        prompt = bridge.get('bridges',{}).get('configuration',{}).get('prompt')
        variables = []
        if prompt is not None:
            variables = Helper.find_variables_in_string(prompt)
        variables_path = bridge.get('bridges').get('variables_path',{})
        path_variables = []
        for script_id, vars_dict in variables_path.items():
            if isinstance(vars_dict, dict):
                path_variables.extend(vars_dict.keys())
            else:
                path_variables.append(vars_dict)
        all_variables = variables + path_variables
        bridge.get('bridges')['all_varaibles'] = all_variables
        response = await Helper.response_middleware_for_bridge(bridge.get('bridges')['service'], {"success": True,"message": "bridge get successfully","bridge":bridge.get("bridges", {})})
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)

async def get_all_bridges(request):
    try:
        org_id = request.state.profile['org']['id']
        folder_id = request.state.folder_id if hasattr(request.state, 'folder_id') else None
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
        isEmbedUser = request.state.embed
        viasocket_embed_user_id = org_id
        if user_id and isEmbedUser and folder_id:
            viasocket_embed_user_id += "_" + folder_id + "_" + user_id
        bridges = await get_all_bridges_in_org(org_id, folder_id, user_id, isEmbedUser)
        embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.PROJECT_ID, "user_id": viasocket_embed_user_id },Config.Access_key )
        alerting_embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.ALERTING_PROJECT_ID, "user_id": viasocket_embed_user_id },Config.Access_key )
        trigger_embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.TRIGGER_PROJECT_ID, "user_id": viasocket_embed_user_id },Config.Access_key )
        history_page_chatbot_token = Helper.generate_token({ "org_id": "11202", "chatbot_id": "67286d4083e482fd5b466b69", "user_id": org_id },Config.CHATBOT_ACCESS_KEY )
        doctstar_embed_token = Helper.generate_token({ "org_id": Config.DOCSTAR_ORG_ID, "collection_id": Config.DOCSTAR_COLLECTION_ID, "user_id": org_id },Config.DOCSTAR_ACCESS_KEY )
        # metrics_data = await get_timescale_data(org_id)
        # bridges = Helper.sort_bridges(bridges, metrics_data)
        avg_response_time = {}
        for bridge in bridges:
            bridge_id = bridge.get('_id')
            avg_response_time_data = await find_in_cache(f"AVG_{org_id}_{bridge_id}")
            lastused = await find_in_cache(f"{redis_keys['bridgelastused_']}{bridge_id}")
            
            # Set last_used from cache, or from database if cache is empty
            if lastused:
                bridge["last_used"] = json.loads(lastused.decode())
            else:
                # Convert datetime object to string when coming from database
                bridge["last_used"] = str(bridge["last_used"]) if bridge.get("last_used") else None

            avg_response_time[bridge_id] = round(float(avg_response_time_data), 2) if avg_response_time_data else 0
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all bridges successfully",
                "bridge" : bridges,
                "embed_token": embed_token,
                "alerting_embed_token": alerting_embed_token,
                "trigger_embed_token": trigger_embed_token,
                "history_page_chatbot_token" : history_page_chatbot_token,
                "doctstar_embed_token" : doctstar_embed_token,
                "org_id": org_id,
                "avg_response_time": avg_response_time
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_all_service_models_controller(service, request):
    try:
        service = service.lower()
        org_id = request.state.profile['org']['id']
        
        def restructure_configuration(config):
            model_field = config.get("configuration", {}).get("model", "")
            additional_parameters = config.get("configuration", {})
            
            return {
                "configuration": {
                    "model": model_field,
                    "additional_parameters": additional_parameters
                },
                "validationConfig" : config.get("validationConfig", {}),
                "outputConfig": config.get('outputConfig',{}),
                "org_id": config.get('org_id', None)
            }
        
        # Check if service exists in model_config_document
        if service not in model_config_document:
            return {}
        
        # Initialize result dictionary with default categories
        result = {
            "chat": {},
            "fine-tune": {},
            "reasoning": {},
            "image": {},
            "embedding": {}
        }
        
        # Iterate through all models in the service
        service_models = model_config_document[service]
        
        for model_name, model_config in service_models.items():
            # Check if model has status and if it equals 1
            if model_config.get('status') != 1:
                continue
            
            # Check if model has org_id and if it doesn't match the current org_id
            if 'org_id' in model_config and model_config['org_id'] != org_id:
                continue  # Skip this model if org_id doesn't match
            
            # Get model type from configuration, default to 'chat' if not specified
            model_type = model_config.get('validationConfig', {}).get('type', 'chat')
            
            # Add the model to appropriate category
            result[model_type][model_name] = restructure_configuration(model_config)
        
        # Remove empty categories
        result = {category: models for category, models in result.items() if models}
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_all_service_models_controller: {e}")
        return {}

async def get_all_service_controller():
    return {
        "success": True,
        "message": "Get all service successfully",
        "services": {
            "openai": {"model": "gpt-4o"},
            "anthropic": {"model": "claude-3-7-sonnet-latest"},
            "groq": {"model": "llama-3.3-70b-versatile"},
            "open_router": {"model": "deepseek/deepseek-chat-v3-0324:free"},
            "mistral": {"model": "mistral-medium-latest"},
            "gemini" : {"model" : "gemini-2.5-flash"},
            "ai_ml" : {"model" : "gpt-oss-20b"}
        }
    }

async def update_bridge_controller(request, bridge_id=None, version_id=None):
    """Update bridge configuration with provided parameters.
    
    Args:
        request: HTTP request object containing user profile and request body
        bridge_id: Optional ID of the bridge to update
        version_id: Optional version ID of the bridge to update
        
    Returns:
        JSON response with updated bridge information
        
    Raises:
        HTTPException: For validation errors or unexpected exceptions
    """
    try:
        # Extract request data
        body = await request.json()
        org_id = request.state.profile['org']['id']
        user_id = request.state.profile['user']['id']
        
        # Get existing bridge data
        bridge = await get_bridge_by_id(org_id, bridge_id, version_id)
        if bridge is None:
            raise HTTPException(status_code=404, detail="Bridge not found")
        parent_id = bridge.get('parent_id')
        current_configuration = bridge.get('configuration', {})
        current_variables_path = bridge.get('variables_path', {})
        function_ids = bridge.get('function_ids') or []
        
        # Initialize update fields and user history tracking
        page_config = body.get('page_config')
        update_fields = {}
        user_history = []
        
        # Extract configuration data
        new_configuration = body.get('configuration')
        config_type = new_configuration.get('type') if new_configuration else None
        service = body.get('service')

        #process connected agent data
        connected_agent_details = body.get('connected_agent_details')
        if connected_agent_details is not None:
            update_fields['connected_agent_details'] = connected_agent_details
        
        # Process API key if provided
        apikey_object_id = body.get('apikey_object_id')
        if apikey_object_id is not None:
            await get_apikey_creds(org_id, apikey_object_id)
            update_fields['apikey_object_id'] = apikey_object_id
        
        # Handle system prompt if present in configuration
        if new_configuration and (prompt := new_configuration.get('prompt')):
            prompt_result = await storeSystemPrompt(prompt, org_id, parent_id if parent_id is not None else version_id)
            new_configuration['system_prompt_version_id'] = prompt_result.get('id')
        
        # Reset fine-tune model for non-fine-tune configurations
        if new_configuration and 'type' in new_configuration and new_configuration.get('type') != 'fine-tune':
            new_configuration['fine_tune_model'] = {'current_model': None}
        
        # Process basic fields
        simple_fields = {
            'bridge_status': lambda v: v in [0, 1],
            'bridge_summary': lambda v: True,
            'expected_qna': lambda v: True,
            'slugName': lambda v: True,
            'tool_call_count': lambda v: True,
            'user_reference': lambda v: True,
            'gpt_memory': lambda v: True,
            'gpt_memory_context': lambda v: True,
            'doc_ids': lambda v: True,
            'variables_state': lambda v: True,
            'IsstarterQuestionEnable': lambda v: True,
            'name': lambda v: True,
            'bridgeType': lambda v: True,
            'meta': lambda v: True,
            'fall_back': lambda v: True,
            'guardrails': lambda v: isinstance(v, dict) and 'is_enabled' in v
        }
        
        # Update simple fields if they exist in the request
        for field, validator in simple_fields.items():
            value = body.get(field)
            if value is not None and validator(value):
                update_fields[field] = value
        
        # Handle service and model configuration
        if page_config is not None:
            update_fields['page_config'] = page_config
        if service is not None:
            update_fields['service'] = service
            if new_configuration and 'model' in new_configuration:
                model = new_configuration['model']
                configuration = await get_default_values_controller(service, model, current_configuration, config_type)
                configuration['type'] = new_configuration.get('type', 'chat')
                new_configuration = configuration
        
        # Process configuration updates
        if new_configuration is not None:
            # If model is changing but service isn't provided, get default values
            if new_configuration.get('model') and service is None:
                service = bridge.get('service')
                model = new_configuration.get('model')
                configuration = await get_default_values_controller(service, model, current_configuration, config_type)
                configuration['type'] = new_configuration.get('type', 'chat')
                new_configuration = {**new_configuration, **configuration}
            
            # Merge configurations and update
            update_fields['configuration'] = {**current_configuration, **new_configuration}
        
        # Process variables path
        variables_path = body.get('variables_path')
        if variables_path is not None:
            updated_variables_path = {**current_variables_path, **variables_path}
            # Convert list values to empty dictionaries
            for key, value in updated_variables_path.items():
                if isinstance(value, list):
                    updated_variables_path[key] = {}
            update_fields['variables_path'] = updated_variables_path
        
        # Process built-in tools
        built_in_tools = body.get('built_in_tools_data', {}).get('built_in_tools')
        built_in_tools_operation = body.get('built_in_tools_data', {}).get('built_in_tools_operation')
        if built_in_tools is not None:
            operation_value = 1 if built_in_tools_operation == '1' else 0
            await update_built_in_tools(version_id, built_in_tools, operation_value)
        
        # Process agents
        agents = body.get('agents')
        if agents is not None:
            connected_agents = agents.get('connected_agents')
            agent_status = agents.get('agent_status')
            if connected_agents is not None:
                operation_value = 1 if agent_status == '1' else 0
                if operation_value == 0 and connected_agents:
                    for agent_name, agent_info in connected_agents.items():
                        if agent_info.get('bridge_id') and agent_info.get('bridge_id') in current_variables_path:
                            del current_variables_path[agent_info.get('bridge_id')]
                            update_fields['variables_path'] = current_variables_path
                await update_agents(version_id, connected_agents, operation_value)
                    
        
        # Process function updates
        function_data = body.get('functionData', {})
        function_id = function_data.get('function_id')
        function_operation = function_data.get('function_operation')
        function_name = function_data.get('function_name')
        
        if function_id is not None:
            id_to_delete = {
                "bridge_ids": [],
                "version_ids": []
            }
            target_id = bridge_id if bridge_id is not None else version_id
            
            if function_operation is not None:  # Add function ID
                if function_id not in function_ids:
                    function_ids.append(function_id)
                    update_fields['function_ids'] = [ObjectId(fid) for fid in function_ids]
                    id_to_delete = await update_bridge_ids_in_api_calls(function_id, target_id, 1)
            else:  # Remove function ID
                if function_name is not None and function_name in current_variables_path:
                    del current_variables_path[function_name]
                    update_fields['variables_path'] = current_variables_path
                
                if function_id in function_ids:
                    function_ids.remove(function_id)
                    update_fields['function_ids'] = [ObjectId(fid) for fid in function_ids]
                    id_to_delete = await update_bridge_ids_in_api_calls(function_id, target_id, 0)
            
            await delete_all_version_and_bridge_ids_from_cache(id_to_delete)
        
        # Build user history entries
        for key, value in body.items():
            history_entry = {
                'user_id': user_id,
                'org_id': org_id,
                'bridge_id': parent_id or '',
                'version_id': version_id
            }
            
            if key == 'configuration':
                for config_key in value.keys():
                    user_history.append({**history_entry, 'type': config_key})
            else:
                user_history.append({**history_entry, 'type': key})
        
        # Handle version information
        version_description = body.get('version_description')
        if version_id is not None:
            if version_description is None:
                update_fields['is_drafted'] = True
            else:
                update_fields['version_description'] = version_description
        
        # Perform database updates
        await update_bridge(bridge_id=bridge_id, update_fields=update_fields, version_id=version_id)
        result = await get_bridges_with_tools(bridge_id, org_id, version_id)
        await add_bulk_user_entries(user_history)
        if apikey_object_id is not None:
            await try_catch(update_apikey_creds, version_id, apikey_object_id)
        
        # Update service in bridge if it was changed
        if service is not None:
            bridge['service'] = service
        
        # Return success response
        if result.get("success"):
            response = await Helper.response_middleware_for_bridge(bridge['service'], {
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge": result.get('bridges')
            }, True)
            return response
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e.json()}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
async def get_all_in_built_tools_controller():
    return {
        "success": True,
        "message": "Get all inbuilt tools successfully",
        "in_built_tools": [
            {
                "id": '1',
                "name": 'Web Search',
                "description": 'Allow models to search the web for the latest information before generating a response.',
                "value": 'web_search'
            },
            {
                "id": '2',
                "name" : "image generation",
                "description": "Allow models to generate images based on the user's input.",
                "value": 'image_generation'
            }
        ]
    }

async def get_all_agents(request):
    # body  = await request.json()
    user_email = request.state.profile.get("userEmail", '')
    result = await get_all_agents_data(user_email)
    return JSONResponse(status_code=200, content=json.loads(json.dumps({
        "success": True,
        "data": result
    }, default=str)))

async def get_agent(request,slug_name):
    # body  = await request.json()
    user_email = request.state.profile.get("userEmail",'')
    result = await get_agents_data(slug_name, user_email)
    return JSONResponse(status_code=200, content=json.loads(json.dumps({
        "success": True,
        "data": result
    }, default=str)))

async def get_bridges_and_versions_by_model_controller(model_name):
    models = await get_bridges_and_versions_by_model(model_name)
    return {
        "success": True,
        "message": "Fetched models and bridges they are used in successfully.",
        model_name: models
    }
    