import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
from bson import ObjectId
from models.mongo_connection import db
from src.services.utils.common_utils import updateVariablesWithTimeZone
from src.services.commonServices.baseService.utils import makeFunctionName
from src.services.utils.service_config_utils import tool_choice_function_name_formatter
import time
apiCallModel = db['apicalls']

# from src.services.commonServices.generateToken import generateToken
# from src.configs.modelConfiguration import ModelsConfig

async def getConfiguration(configuration, service, bridge_id, apikey, template_id=None, variables = {}, org_id="", variables_path = None, version_id=None, extra_tools=[], built_in_tools = [], initGetConfig={}):
    RTLayer = False
    bridge = None
    initGetConfig['startGetConfig'] = time.time()
    initGetConfig["beforeconfigAndTool"] = time.time()
    result = await ConfigurationService.get_bridges_with_tools_and_apikeys(bridge_id = bridge_id, org_id = org_id, version_id=version_id)
    initGetConfig["afterconfigAndTool"] = time.time()
    bridge_id = bridge_id or result.get('bridges', {}).get('parent_id')
    initGetConfig["beforebridgecheck"] = time.time()
    if version_id : bridge_data = await ConfigurationService.get_bridges_with_redis(bridge_id = bridge_id, org_id = org_id)
    else : bridge_data = result
    initGetConfig["afterbridgecheck"] = time.time()
    bridge_status = bridge_data.get('bridges',{}).get('bridge_status')
    if(bridge_status == 0):
        raise Exception("Bridge is Currently Paused")
    if not result['success']:
        return {
            'success': False,
            'error': "bridge_id does not exist"
        }
    db_configuration = result.get('bridges', {}).get('configuration', {})
    service = service or (result.get('bridges', {}).get('service', '').lower())
    if configuration:
        db_configuration.update(configuration)
    configuration = db_configuration
    
    tool_choice_ids = configuration.get('tool_choice', [])
    toolchoice = None
    initGetConfig["beforetoolcofig"] = time.time()
    for key, api_data in result.get('bridges', {}).get('apiCalls', {}).items():
        if api_data['_id'] in tool_choice_ids:
            toolchoice = makeFunctionName(api_data['endpoint_name'] or api_data['function_name'])
            break
            
    found_choice = None
    for choice in ['auto', 'none', 'required', 'default', 'any']:
        if choice in tool_choice_ids:
            found_choice = choice
            break
    configuration['tool_choice'] = tool_choice_function_name_formatter(service, configuration, toolchoice, found_choice)
    bridge = result.get('bridges')
    variables_path_bridge = bridge.get('variables_path', {})
    # make tools data
    tools = []
    tool_id_and_name_mapping = {}
    initGetConfig["aftertoolconfig"] = time.time()
    for key, api_data in result.get('bridges', {}).get('apiCalls', {}).items():
        # if status is paused then only don't include it in tools
        name_of_function = makeFunctionName(api_data.get('endpoint_name') or  api_data.get("function_name"))
        tool_id_and_name_mapping[name_of_function] =  {
            "url": f"https://flow.sokt.io/func/{api_data.get('function_name')}",
            "headers":{},
            "name": api_data.get('function_name')
        }
        variablesFillByGtwy = list(variables_path_bridge.get(api_data.get("function_name"), {}).keys())
        properties = (
                api_data.get("fields", {}) if api_data.get("version") == 'v2' 
                else {item["variable_name"]: {
                    "description": item.get("description", ""), 
                    "enum": [] if(item.get("enum") == '') else item.get("enum", []),
                    "type": "string",
                    "parameter": {}
                } for item in api_data.get('fields',{})}
            )
        for key in variablesFillByGtwy:
            properties.pop(key, None)
        required = api_data.get("required_params")
        required = [key for key in required if key not in variablesFillByGtwy]

        if api_data.get('status') == 0 and not name_of_function:
            continue
        format = {
            "type": "function",
            "name": name_of_function,
            "description": api_data.get('description'),
            "properties": properties,
            "required": required
        }
        tools.append(format)

    for tool in extra_tools:
        if isinstance(tool, dict):
            if tool.get("url"):
                tools.append( {
                        "type": "function",
                        "name": makeFunctionName(tool.get('name')),
                        "description": tool.get('description'),
                        "properties":  tool.get('fields', {}),
                        "required": tool.get("required_params",[])
                    })
                tool_id_and_name_mapping[makeFunctionName(tool.get('name'))] = {
                    "url": tool.get("url"),
                    "headers": tool.get("headers", {})
            }
    initGetConfig["aftertoolconfig"] = time.time()
    configuration.pop('tools', None)
    configuration['tools'] = tools
    service = service.lower() if service else ""
    gpt_memory = result.get('bridges', {}).get('gpt_memory')
    db_apikeys = result.get('bridges', {}).get('apikeys')
    db_api_key = db_apikeys.get(service)
    if service == 'openai_response':
        db_api_key = db_apikeys.get('openai')
    apikey_object_id = result.get('bridges', {}).get('apikey_object_id')
    if not (apikey or db_api_key): 
        raise Exception('Could not find api key')
    apikey = apikey if apikey else Helper.decrypt(db_api_key)
    RTLayer = True if configuration and 'RTLayer' in configuration else False 
    initGetConfig["beforeGetTemplate"] = time.time()
    template_content = await ConfigurationService.get_template_by_id(template_id) if template_id else None
    initGetConfig["afterGetTemplate"] = time.time()
    pre_tools = bridge.get('pre_tools', [])
    gpt_memory_context = bridge.get('gpt_memory_context')
    initGetConfig["beforepretooldb"] = time.time()

    if len(pre_tools)>0:
        api_data = await apiCallModel.find_one({"_id": ObjectId( pre_tools[0]), "org_id": org_id})

        if api_data is None: 
            raise Exception("Didn't find the pre_function")
        name = api_data.get('function_name',api_data.get('endpoint_name',""))
        required_params = api_data.get('required_params', [])
        args = {}
        for param in required_params:
            if param in variables :
                args[param] = variables[param]
    rag_data = bridge.get('rag_data')
    initGetConfig["afterpretooldb"] = time.time()
    tone = configuration.get('tone' , {})
    responseStyle = configuration.get('responseStyle' , {})

    configuration['prompt'] = Helper.append_tone_and_response_style_prompts(configuration['prompt'], tone, responseStyle)

    if rag_data is not None and rag_data != []:
        tools.append({'type': 'function', 'name': 'get_knowledge_base_data', 'description': "When user want to take any data from the knowledge, Call this function to get the corresponding document using document id.", 'properties': {
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
            }, 'required': ['Document_id', 'query']})

        tool_id_and_name_mapping['get_knowledge_base_data'] = {
                "type": "RAG"
            }
    if service == 'anthropic' and isinstance(configuration.get('response_type'), dict) and configuration['response_type'].get('json_schema'):
        required = configuration.get('response_type').get('json_schema').get('required') or []
        if configuration['response_type']['json_schema'].get('required') is not None:
            del configuration['response_type']['json_schema']['required']
        tools.append({
        "name": "JSON_Schema_Response_Format",
        "description": "return the response in json schema format",
        "input_schema": configuration.get('response_type').get('json_schema').get('schema')
      })
        configuration['response_type'] = 'default'
        configuration['prompt'] += '\n Always return the response in JSON SChema by calling the function JSON_Schema_Response_Format and if no values available then return json with dummy or default vaules'

    configuration['prompt'] = Helper.add_doc_description_to_prompt(configuration['prompt'], rag_data)
    variables, org_name = await updateVariablesWithTimeZone(variables,org_id)
    initGetConfig["endGetconfig"] = time.time()
    return {
        'success': True,
        'configuration': configuration,
        'pre_tools': {'name': name, 'args': args} if len(pre_tools)>0 else None,
        'service': service,
        'apikey': apikey,
        'apikey_object_id': apikey_object_id,
        'RTLayer': RTLayer,
        'template': template_content.get('template') if template_content else None,
        "user_reference": result.get("bridges", {}).get("user_reference", ""),
        "variables_path": variables_path or variables_path_bridge,
        "tool_id_and_name_mapping":tool_id_and_name_mapping,
        "gpt_memory" : gpt_memory,
        "version_id" : version_id or result.get('bridges', {}).get('published_version_id'),
        "gpt_memory_context" :  gpt_memory_context,
        "tool_call_count": result.get("bridges", {}).get("tool_call_count", 3),
        "variables": variables,
        "rag_data":rag_data,
        "actions": result.get("bridges", {}).get("actions", []),
        "name" : result.get("bridges", {}).get("name") or '',
        "org_name" : org_name,
        "bridge_id" : result['bridges'].get('parent_id', result['bridges'].get('_id')),
        "variables_state" : result.get("bridges", {}).get("variables_state", {}),
        "built_in_tools" :  built_in_tools or result.get("bridges", {}).get("built_in_tools"),
    }
