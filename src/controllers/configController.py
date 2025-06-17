from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.db_services.ConfigurationServices import create_bridge, get_bridge_by_id, get_all_bridges_in_org, update_bridge, update_bridge_ids_in_api_calls, get_bridges_with_tools, get_apikey_creds, update_apikey_creds, update_built_in_tools, update_agents
from src.configs.modelConfiguration import ModelsConfig as model_configuration
from src.services.utils.helper import Helper
import json
from config import Config
from ..configs.constant import service_name
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
            service = bridges.get('service')
            model = bridges.get('model')
            name = bridges.get('name')
            type = bridges.get('type')
            slugName = bridges.get('slugName')
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
        model_data["is_rich_text"]= True
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
            "gpt_memory" : True
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
        return Helper.response_middleware_for_bridge(bridge.get('bridges')['service'], {"succcess": True,"message": "bridge get successfully","bridge":bridge.get("bridges", {})})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)

async def get_all_bridges(request):
    try:
        org_id = request.state.profile['org']['id']
        bridges = await get_all_bridges_in_org(org_id)
        embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.PROJECT_ID, "user_id": org_id },Config.Access_key )
        alerting_embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.ALERTING_PROJECT_ID, "user_id": org_id },Config.Access_key )
        trigger_embed_token = Helper.generate_token({ "org_id": Config.ORG_ID, "project_id": Config.TRIGGER_PROJECT_ID, "user_id": org_id },Config.Access_key )
        history_page_chatbot_token = Helper.generate_token({ "org_id": "11202", "chatbot_id": "67286d4083e482fd5b466b69", "user_id": org_id },Config.CHATBOT_ACCESS_KEY )
        # metrics_data = await get_timescale_data(org_id)
        # bridges = Helper.sort_bridges(bridges, metrics_data)
        avg_response_time = {}
        for bridge in bridges:
            bridge_id = bridge.get('_id')
            avg_response_time_data = await find_in_cache(f"AVG_{org_id}_{bridge_id}")
            avg_response_time[bridge_id] = round(float(avg_response_time_data), 2) if avg_response_time_data else 0
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all bridges successfully",
                "bridge" : bridges,
                "embed_token": embed_token,
                "alerting_embed_token": alerting_embed_token,
                "trigger_embed_token": trigger_embed_token,
                "history_page_chatbot_token" : history_page_chatbot_token,
                "org_id": org_id,
                "avg_response_time": avg_response_time
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_all_service_models_controller(service):
    try:
        service = service.lower()
        
        def restructure_configuration(config):
            model_field = config.get("configuration", {}).get("model", "")
            additional_parameters = config.get("configuration", {})
            
            return {
                "configuration": {
                    "model": model_field,
                    "additional_parameters": additional_parameters
                }
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
        "services": ['openai', 'anthropic', 'groq', 'openai_response', 'open_router']
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
        parent_id = bridge.get('parent_id')
        current_configuration = bridge.get('configuration', {})
        current_variables_path = bridge.get('variables_path', {})
        function_ids = bridge.get('function_ids') or []
        
        # Initialize update fields and user history tracking
        update_fields = {}
        user_history = []
        
        # Extract configuration data
        new_configuration = body.get('configuration')
        config_type = new_configuration.get('type') if new_configuration else None
        service = body.get('service')
        
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
            'bridgeType': lambda v: True
        }
        
        # Update simple fields if they exist in the request
        for field, validator in simple_fields.items():
            value = body.get(field)
            if value is not None and validator(value):
                update_fields[field] = value
        
        # Handle service and model configuration
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
        await try_catch(update_apikey_creds, version_id)
        
        # Update service in bridge if it was changed
        if service is not None:
            bridge['service'] = service
        
        # Return success response
        if result.get("success"):
            return Helper.response_middleware_for_bridge(bridge['service'], {
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge": result.get('bridges')
            })
        
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
            }
        ]
    }
