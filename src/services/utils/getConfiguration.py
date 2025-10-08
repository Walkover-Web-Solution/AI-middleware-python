import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
from models.mongo_connection import db
from src.services.utils.common_utils import updateVariablesWithTimeZone
from .getConfiguration_utils import (
    validate_bridge, get_bridge_data, setup_configuration, setup_tool_choice,
    setup_tools, setup_api_key, setup_pre_tools, add_rag_tool,
    add_anthropic_json_schema, add_connected_agents
)
from src.services.cache_service import store_in_cache, find_in_cache, delete_in_cache
import json
from fastapi import HTTPException
apiCallModel = db['apicalls']
from globals import *
from src.configs.constant import redis_keys

async def getConfiguration(configuration, service, bridge_id, apikey, template_id=None, variables={}, 
                           org_id="", variables_path=None, version_id=None, extra_tools=[], built_in_tools=[], guardrails={}):
    """
    Get configuration for a bridge with all necessary tools and settings.
    
    Args:
        configuration: Configuration to merge with database configuration
        service: Service name
        bridge_id: Bridge ID
        apikey: API key
        template_id: Template ID
        variables: Variables to use
        org_id: Organization ID
        variables_path: Variables path
        version_id: Version ID
        extra_tools: Extra tools to include
        built_in_tools: Built-in tools to include
        
    Returns:
        Dictionary with configuration and related data
    """
    # Initialize variables
    RTLayer = False
    
    # Get bridge data
    result, bridge_data, bridge_id = await get_bridge_data(bridge_id, org_id, version_id)
    
    # Validate bridge
    validation_result = await validate_bridge(bridge_data, result)
    if validation_result:
        return validation_result
    
    # Get and check Bridge quota limit
    bridge_cache_key = f"{redis_keys['bridge_quota']}_{bridge_id}"
    bridge_quota = await find_in_cache(bridge_cache_key)
    bridge_quota = json.loads(bridge_quota.decode("utf-8")) if isinstance(bridge_quota, bytes) else bridge_quota
    bridge_quota =  bridge_quota if bridge_quota is not None else bridge_data.get(f'{redis_keys['bridge_quota']}', {})
    if bridge_quota is not None and len(bridge_quota) > 0:
        await store_in_cache(bridge_cache_key, bridge_quota) 
    # Handle if bridge quota is a bytes object
    
    if bridge_quota and 'limit' in bridge_quota and 'used' in bridge_quota and (int(bridge_quota['limit']) <= int(bridge_quota['used'])):
        raise HTTPException(status_code=429, detail="Bridge quota limit reached for the bridge.")
    
    # Get and check API keys quota limit
    bridge_doc = result.get('bridges')
    if bridge_doc:
        apikey_data = bridge_doc.get('apikey_object_id')
        if apikey_data:
            service_name = []
            items_to_iterate = []
            if isinstance(apikey_data, dict):
                items_to_iterate = apikey_data.items()
            elif isinstance(apikey_data, str):
                primary_service = bridge_doc.get('service')
                if primary_service:
                    items_to_iterate = [(primary_service, apikey_data)]

            for service, apikey_object_id in items_to_iterate:
                if not apikey_object_id: continue

                apikey_cache_key = f"{redis_keys['apikey_quota']}_{apikey_object_id}"
                apikey_cache_quota = await find_in_cache(apikey_cache_key)
                apikey_cache_quota = json.loads(apikey_cache_quota.decode("utf-8")) if isinstance(apikey_cache_quota, bytes) else apikey_cache_quota
                
                if apikey_cache_quota is not None:
                    apikey_quota = apikey_cache_quota
                else:
                    apikey_doc = await ConfigurationService.get_apikey_creds(org_id, apikey_object_id)
                    apikey_quota = apikey_doc.get(redis_keys['apikey_quota'], {}) if apikey_doc else {}
                if apikey_quota:
                    await store_in_cache(apikey_cache_key, apikey_quota)
                    if 'limit' in apikey_quota and 'used' in apikey_quota and (int(apikey_quota['limit']) <= int(apikey_quota['used'])):
                        service_name.append(service)

            if len(service_name) > 0:
                raise HTTPException(status_code=429, detail=f"API key quota limit reached for the API key used of service/s: {', '.join(service_name)}")
    # Setup configuration
    configuration, service = setup_configuration(configuration, result, service)

    if service == 'openai_response':   
        service = 'openai'
    if bridge_data.get('bridges', {}).get('openai_completion'):
        service = 'openai_completion'     

    # Setup API key
    service = service.lower() if service else ""
    apikey = setup_api_key(service, result, apikey)
    apikey_object_id = result.get('bridges', {}).get('apikey_object_id')

    # check type
    if configuration['type'] == 'image':
        return{
        'success': True,
        'configuration': configuration,
        'service': service,
        'apikey': apikey,
        'apikey_object_id': apikey_object_id,
        'RTLayer': RTLayer,
        "bridge_id": result['bridges'].get('parent_id', result['bridges'].get('_id')),
        "version_id": version_id or result.get('bridges', {}).get('published_version_id'),
        }
    
    # Setup tool choice
    configuration['tool_choice'] = setup_tool_choice(configuration, result, service)
    
    # Get bridge and variables path
    bridge = result.get('bridges')
    variables_path_bridge = bridge.get('variables_path', {})
    
    # Setup tools and tool mappings
    tools, tool_id_and_name_mapping, variables_path_bridge = setup_tools(result, variables_path_bridge, extra_tools)
    configuration.pop('tools', None)
    configuration['tools'] = tools
    
    # Check for RTLayer
    RTLayer = True if configuration and 'RTLayer' in configuration else False
    
    # Get template content
    template_content = await ConfigurationService.get_template_by_id(template_id) if template_id else None
    
    # Setup pre-tools
    pre_tools_name, pre_tools_args = setup_pre_tools(bridge, result, variables)
    
    # Get RAG data and memory context
    rag_data = bridge.get('rag_data')
    gpt_memory_context = bridge.get('gpt_memory_context')
    gpt_memory = result.get('bridges', {}).get('gpt_memory')
    
    # Apply tone and response style
    tone = configuration.get('tone', {})
    responseStyle = configuration.get('responseStyle', {})
    configuration['prompt'] = Helper.append_tone_and_response_style_prompts(
        configuration['prompt'], tone, responseStyle
    )
    
    # Add RAG tool if needed
    add_rag_tool(tools, tool_id_and_name_mapping, rag_data)
    
    # Add Anthropic JSON schema if needed
    add_anthropic_json_schema(service, configuration, tools)
    
    # Add document description to prompt
    if rag_data:
        configuration['prompt'] = Helper.add_doc_description_to_prompt(configuration['prompt'], rag_data)
    
    # Update variables with timezone
    variables, org_name = await updateVariablesWithTimeZone(variables, org_id)
    
    # Add connected agents
    add_connected_agents(result, tools, tool_id_and_name_mapping)

    # Return final configuration
    return {
        'success': True,
        'configuration': configuration,
        'pre_tools': {'name': pre_tools_name, 'args': pre_tools_args} if pre_tools_name else None,
        'service': service,
        'apikey': apikey,
        'apikey_object_id': apikey_object_id,
        'RTLayer': RTLayer,
        'template': template_content.get('template') if template_content else None,
        "user_reference": result.get("bridges", {}).get("user_reference", ""),
        "variables_path": variables_path or variables_path_bridge,
        "tool_id_and_name_mapping": tool_id_and_name_mapping,
        "gpt_memory": gpt_memory,
        "version_id": version_id or result.get('bridges', {}).get('published_version_id'),
        "gpt_memory_context": gpt_memory_context,
        "tool_call_count": result.get("bridges", {}).get("tool_call_count", 3),
        "variables": variables,
        "rag_data": rag_data,
        "actions": result.get("bridges", {}).get("actions", []),
        "name": result.get("bridges", {}).get("name") or '',
        "org_name": org_name,
        "bridge_id": result['bridges'].get('parent_id', result['bridges'].get('_id')),
        "variables_state": result.get("bridges", {}).get("variables_state", {}),
        "built_in_tools": built_in_tools or result.get("bridges", {}).get("built_in_tools"),
        "fall_back" : result.get("bridges", {}).get("fall_back") or {},
        "guardrails" : guardrails if guardrails is not None else (result.get("bridges", {}).get("guardrails") or {}),
    }

