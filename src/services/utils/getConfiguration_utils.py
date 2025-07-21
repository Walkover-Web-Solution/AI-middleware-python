import src.db_services.ConfigurationServices as ConfigurationService
from src.services.utils.helper import Helper
from bson import ObjectId
from models.mongo_connection import db
from src.services.utils.common_utils import updateVariablesWithTimeZone
from src.services.commonServices.baseService.utils import makeFunctionName
from src.services.utils.service_config_utils import tool_choice_function_name_formatter

apiCallModel = db['apicalls']
from globals import *

async def validate_bridge(bridge_data, result):
    """Validate bridge status and existence"""
    bridge_status = bridge_data.get('bridges', {}).get('bridge_status') or bridge_data.get('bridge_status')
    if bridge_status == 0:
        raise Exception("Bridge is Currently Paused")
    
    if not result.get('success'):
        return {
            'success': False,
            'error': "bridge_id does not exist"
        }
    return None

async def get_bridge_data(bridge_id, org_id, version_id):
    """Fetch bridge data from database"""
    result = await ConfigurationService.get_bridges_with_tools_and_apikeys(
        bridge_id=bridge_id, 
        org_id=org_id, 
        version_id=version_id
    )
    
    bridge_id = bridge_id or result.get('bridges', {}).get('parent_id')
    
    if version_id:
        bridge_data = await ConfigurationService.get_bridges_with_redis(
            bridge_id=bridge_id, 
            org_id=org_id
        )
    else:
        bridge_data = result
        
    return result, bridge_data, bridge_id

def setup_configuration(configuration, result, service):
    """Setup and merge configuration from database and input"""
    db_configuration = result.get('bridges', {}).get('configuration', {})
    service = service or (result.get('bridges', {}).get('service', '').lower())
    
    if configuration:
        db_configuration.update(configuration)
    
    return db_configuration, service

def setup_tool_choice(configuration, result, service):
    """Setup tool choice configuration"""
    tool_choice_ids = configuration.get('tool_choice', [])
    toolchoice = None
    
    # Find tool choice from API calls
    for _, api_data in result.get('bridges', {}).get('apiCalls', {}).items():
        if api_data['_id'] in tool_choice_ids:
            toolchoice = makeFunctionName(api_data['endpoint_name'] or api_data['function_name'])
            break
    
    # Find choice type
    found_choice = None
    for choice in ['auto', 'none', 'required', 'default', 'any']:
        if choice in tool_choice_ids:
            found_choice = choice
            break
    
    return tool_choice_function_name_formatter(
        service=service, 
        configuration=configuration, 
        toolchoice=toolchoice, 
        found_choice=found_choice
    )

def process_api_call_tool(api_data, variables_path_bridge):
    """Process a single API call and convert it to a tool format"""
    name_of_function = makeFunctionName(api_data.get('endpoint_name') or api_data.get("function_name"))
    
    # Skip if status is paused and no function name
    if api_data.get('status') == 0 and not name_of_function:
        return None, None
    
    # Setup tool mapping
    tool_mapping = {
        "url": f"https://flow.sokt.io/func/{api_data.get('function_name')}",
        "headers": {},
        "name": api_data.get('function_name')
    }
    
    # Process variables filled by gateway
    variables_fill_by_gtwy = list(variables_path_bridge.get(api_data.get("function_name"), {}).keys())
    
    # Process properties based on version
    if api_data.get("version") == 'v2':
        properties = api_data.get("fields", {})
    else:
        properties = {
            item["variable_name"]: {
                "description": item.get("description", ""), 
                "enum": [] if(item.get("enum") == '') else item.get("enum", []),
                "type": "string",
                "parameter": {}
            } for item in api_data.get('fields', {})
        }
    
    # Remove properties that are filled by gateway
    for key in variables_fill_by_gtwy:
        properties.pop(key, None)
    
    # Filter required parameters
    required = api_data.get("required_params", [])
    required = [key for key in required if key not in variables_fill_by_gtwy]
    
    # Create tool format
    tool_format = {
        "type": "function",
        "name": name_of_function,
        "description": api_data.get('description'),
        "properties": properties,
        "required": required
    }
    
    return tool_format, tool_mapping

def process_extra_tool(tool):
    """Process an extra tool and convert it to tool format"""
    if not isinstance(tool, dict) or not tool.get("url"):
        return None, None
    
    tool_format = {
        "type": "function",
        "name": makeFunctionName(tool.get('name')),
        "description": tool.get('description'),
        "properties": tool.get('fields', {}),
        "required": tool.get("required_params", [])
    }
    
    tool_mapping = {
        "url": tool.get("url"),
        "headers": tool.get("headers", {})
    }
    
    return tool_format, tool_mapping

def setup_tools(result, variables_path_bridge, extra_tools):
    """Setup tools and tool mappings"""
    tools = []
    tool_id_and_name_mapping = {}
    
    # Process API calls
    for _, api_data in result.get('bridges', {}).get('apiCalls', {}).items():
        tool_format, tool_mapping = process_api_call_tool(api_data, variables_path_bridge)
        if tool_format:
            name_of_function = tool_format["name"]
            tools.append(tool_format)
            tool_id_and_name_mapping[name_of_function] = tool_mapping
    
    # Process extra tools
    for tool in extra_tools:
        tool_format, tool_mapping = process_extra_tool(tool)
        if tool_format:
            name_of_function = tool_format["name"]
            tools.append(tool_format)
            tool_id_and_name_mapping[name_of_function] = tool_mapping
    
    return tools, tool_id_and_name_mapping

def setup_api_key(service, result, apikey):
    """Setup API key for the service"""
    db_apikeys = result.get('bridges', {}).get('apikeys', {})
    
    # Get API key for the service
    db_api_key = db_apikeys.get(service)
    if service == 'openai_response':
        db_api_key = db_apikeys.get('openai')
    
    # Validate API key existence
    if not (apikey or db_api_key):
        raise Exception('Could not find api key or Agent is not Published')
    
    # Use provided API key or decrypt from database
    return apikey if apikey else Helper.decrypt(db_api_key)

def setup_pre_tools(bridge, result, variables):
    """Setup pre-tools configuration"""
    pre_tools = bridge.get('pre_tools', [])
    if not pre_tools:
        return None, None
    
    api_data = result.get('bridges', {}).get('pre_tools_data', [{}])[0]
    if api_data is None:
        raise Exception("Didn't find the pre_function")
    
    name = api_data.get('function_name', api_data.get('endpoint_name', ""))
    required_params = api_data.get('required_params', [])
    
    args = {}
    for param in required_params:
        if param in variables:
            args[param] = variables[param]
    
    return name, args

def add_rag_tool(tools, tool_id_and_name_mapping, rag_data):
    """Add RAG tool if RAG data is available"""
    if not rag_data or rag_data == []:
        return
    
    tools.append({
        'type': 'function', 
        'name': 'get_knowledge_base_data', 
        'description': "When user want to take any data from the knowledge, Call this function to get the corresponding document using document id.", 
        'properties': {
            "Document_id": {
                "description": "document id as per your requirement",
                "type": "string",
                "enum": [],
                "required_params": [],
                "parameter": {}
            },
            "query": {
                "description": "query",
                "type": "string",
                "enum": [],
                "required_params": [],
                "parameter": {}
            }
        }, 
        'required': ['Document_id', 'query']
    })
    
    tool_id_and_name_mapping['get_knowledge_base_data'] = {
        "type": "RAG"
    }

def add_anthropic_json_schema(service, configuration, tools):
    """Add JSON schema response format for Anthropic service"""
    if (service != 'anthropic' or 
        not isinstance(configuration.get('response_type'), dict) or 
        not configuration['response_type'].get('json_schema')):
        return
    
    # Remove required field if it exists
    if configuration['response_type']['json_schema'].get('required') is not None:
        del configuration['response_type']['json_schema']['required']
    
    # Add JSON schema tool
    tools.append({
        "name": "JSON_Schema_Response_Format",
        "description": "return the response in json schema format",
        "input_schema": configuration.get('response_type').get('json_schema').get('schema')
    })
    
    # Update configuration
    configuration['response_type'] = 'default'
    configuration['prompt'] += '\n Always return the response in JSON SChema by calling the function JSON_Schema_Response_Format and if no values available then return json with dummy or default vaules'

def add_connected_agents(result, tools, tool_id_and_name_mapping):
    """Add connected agents as tools"""
    connected_agents = result.get('bridges', {}).get('connected_agents', {})
    if not connected_agents:
        return
    
    for bridge_name, bridge_info in connected_agents.items():
        id = bridge_info.get('bridge_id', '')
        description = bridge_info.get('description', '')
        variables = bridge_info.get('variables', {})
        fields = variables.get('fields', {})
        name = makeFunctionName(bridge_name)

        
        tools.append({
            "type": "function",
            "name": name,
            "description": description,
            "properties": {
                "user": {
                    "description": "this is the query for the agent to process the request",
                    "type": "string",
                    "enum": [],
                    "required_params": [],
                    "parameter": {}
                },
                **fields
            },
            "required": ["user"] + variables.get('required_params', [])
        })
        
        tool_id_and_name_mapping[name] = {
            "type": "AGENT",
            "bridge_id": id
        }
