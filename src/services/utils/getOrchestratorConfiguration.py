import asyncio
import src.db_services.ConfigurationServices as ConfigurationService
import src.db_services.OrchestratorServices as OrchestratorService
from .helper import Helper
from models.mongo_connection import db
from src.services.utils.common_utils import updateVariablesWithTimeZone
from .getConfiguration_utils import (
    validate_bridge, get_bridge_data, setup_configuration, setup_tool_choice,
    setup_tools, setup_api_key, setup_pre_tools, add_rag_tool,
    add_anthropic_json_schema, add_connected_agents
)
from src.services.utils.logger import logger
from globals import *

async def getOrchestratorConfiguration(orchestrator_id, org_id, variables={}, variables_path=None):
    """
    Get configuration for an orchestrator with all agent data and settings.
    
    Args:
        configuration: Configuration to merge with database configuration
        service: Service name
        orchestrator_id: Orchestrator ID
        apikey: API key
        template_id: Template ID
        variables: Variables to use
        org_id: Organization ID
        variables_path: Variables path
        version_id: Version ID
        extra_tools: Extra tools to include
        built_in_tools: Built-in tools to include
        
    Returns:
        Dictionary with orchestrator configuration and all agent data
    """
    try:
        # Get orchestrator data
        orchestrator_data = await OrchestratorService.get_orchestrator_by_id(orchestrator_id, org_id)
        if not orchestrator_data:
            return {
                'success': False,
                'error': 'Orchestrator not found'
            }
        
        # Extract agents from orchestrator
        agents = orchestrator_data.get('agents', {})
        master_agent_id = orchestrator_data.get('master_agent')
        
        if not agents:
            return {
                'success': False,
                'error': 'No agents found in orchestrator'
            }
        
        # Get agent configurations in parallel
        async def process_agent(agent_id, agent_info):
            """Process a single agent configuration"""
            try:
                # Use the existing pipeline to get bridge data for each agent
                # The agent_id should be the bridge_id in the database
                bridge_result = await ConfigurationService.get_bridges_with_tools_and_apikeys(
                    agent_id, org_id
                )
                
                if bridge_result.get('success'):
                    # Transform the bridge data using getConfiguration logic with agent-specific values
                    agent_config = await transform_agent_configuration(bridge_result, variables, org_id, variables_path)
                    
                    # Add agent metadata
                    agent_config['agent_info'] = {
                        'name': agent_info.get('name'),
                        'description': agent_info.get('description'),
                        'parentAgents': agent_info.get('parentAgents', []),
                        'childAgents': agent_info.get('childAgents', []),
                        'variables': agent_info.get('variables', {})
                    }
                    
                    return agent_id, agent_config
                else:
                    logger.warning(f"Failed to get bridge data for agent {agent_id}: {bridge_result.get('error')}")
                    return agent_id, None
                    
            except Exception as e:
                logger.error(f"Error processing agent {agent_id}: {str(e)}")
                return agent_id, None
        
        # Process all agents in parallel
        agent_tasks = [process_agent(agent_id, agent_info) for agent_id, agent_info in agents.items()]
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Build agent_configurations dict from results
        agent_configurations = {}
        for result in agent_results:
            if isinstance(result, Exception):
                logger.error(f"Exception in parallel agent processing: {result}")
                continue
            
            agent_id, agent_config = result
            if agent_config is not None:
                agent_configurations[agent_id] = agent_config
        
        # Get master agent configuration
        master_agent_config = agent_configurations.get(master_agent_id)
        if not master_agent_config:
            return {
                'success': False,
                'error': f'Master agent {master_agent_id} configuration not found'
            }
        
        # Return orchestrator configuration
        return {
            'success': True,
            'orchestrator_id': orchestrator_id,
            'orchestrator_data': orchestrator_data,
            'master_agent_id': master_agent_id,
            'master_agent_config': master_agent_config,
            'agent_configurations': agent_configurations,
            'agents_count': len(agent_configurations),
            'status': orchestrator_data.get('status'),
            'org_id': org_id
        }
        
    except Exception as e:
        logger.error(f"Error in getOrchestratorConfiguration: {str(e)}")
        return {
            'success': False,
            'error': f'Error getting orchestrator configuration: {str(e)}'
        }

async def transform_agent_configuration(result, variables={}, org_id="", variables_path=None):
    """
    Transform bridge result into agent configuration similar to getConfiguration.
    """
    try:
        # Initialize variables
        RTLayer = False
        configuration = result.get('configuration')
        service = result.get('service')
        # Validate bridge
        validation_result = await validate_bridge(result.get('bridges'), result)
        if validation_result:
            return validation_result
        
        # Setup configuration
        configuration, service = setup_configuration(configuration, result, service)

        # Setup API key
        service = service.lower() if service else ""
        apikey = setup_api_key(service, result, None)
        apikey_object_id = result.get('bridges', {}).get('apikey_object_id')

        # Check type
        if configuration.get('type') == 'image':
            return {
                'success': True,
                'configuration': configuration,
                'service': service,
                'apikey': apikey,
                'apikey_object_id': apikey_object_id,
                'RTLayer': RTLayer,
                "bridge_id": result['bridges'].get('parent_id', result['bridges'].get('_id')),

            }
        
        # Setup tool choice
        configuration['tool_choice'] = setup_tool_choice(configuration, result, service)
        
        # Get bridge and variables path
        bridge = result.get('bridges')
        variables_path_bridge = bridge.get('variables_path', {})
        
        # Setup tools and tool mappings
        tools, tool_id_and_name_mapping = setup_tools(result, variables_path_bridge, [])
        configuration.pop('tools', None)
        configuration['tools'] = tools
        
        # Check for RTLayer
        RTLayer = True if configuration and 'RTLayer' in configuration else False
        
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
        
        # Return agent configuration
        return {
            'success': True,
            'configuration': configuration,
            'pre_tools': {'name': pre_tools_name, 'args': pre_tools_args} if pre_tools_name else None,
            'service': service,
            'apikey': apikey,
            'apikey_object_id': apikey_object_id,
            'RTLayer': RTLayer,
            "user_reference": result.get("bridges", {}).get("user_reference", ""),
            "variables_path": variables_path or variables_path_bridge,
            "tool_id_and_name_mapping": tool_id_and_name_mapping,
            "gpt_memory": gpt_memory,
            "gpt_memory_context": gpt_memory_context,
            "tool_call_count": result.get("bridges", {}).get("tool_call_count", 3),
            "variables": variables,
            "rag_data": rag_data,
            "actions": result.get("bridges", {}).get("actions", []),
            "name": result.get("bridges", {}).get("name") or '',
            "org_name": org_name,
            "bridge_id": result['bridges'].get('parent_id', result['bridges'].get('_id')),
            "variables_state": result.get("bridges", {}).get("variables_state", {})
        }
        
    except Exception as e:
        logger.error(f"Error in transform_agent_configuration: {str(e)}")
        return {
            'success': False,
            'error': f'Error transforming agent configuration: {str(e)}'
        }
