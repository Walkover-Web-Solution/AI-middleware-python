import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
from bson import ObjectId
from models.mongo_connection import db
from src.services.utils.common_utils import updateVariablesWithTimeZone
from src.services.commonServices.baseService.utils import makeFunctionName
apiCallModel = db['apicalls']

# from src.services.commonServices.generateToken import generateToken
# from src.configs.modelConfiguration import ModelsConfig

async def getConfiguration(configuration, service, bridge_id, apikey, template_id=None, variables = {}, org_id="", variables_path = None, version_id=None, extra_tools=[]):
    RTLayer = False
    bridge = None
    result = await ConfigurationService.get_bridges_with_tools_and_apikeys(bridge_id = bridge_id, org_id = org_id, version_id=version_id)
    if not result['success']:
        return {
            'success': False,
            'error': "bridge_id does not exist"
        }
    db_configuration = result.get('bridges', {}).get('configuration', {})
    if configuration:
        db_configuration.update(configuration)
    configuration = db_configuration
    
    # make tools data
    tools = []
    tool_id_and_name_mapping = {}
    for key, api_data in result.get('bridges', {}).get('apiCalls', {}).items():
        # if status is paused then only don't include it in tools
        name_of_function = makeFunctionName(api_data.get("function_name"))
        tool_id_and_name_mapping[name_of_function] =  {
            "url": f"https://flow.sokt.io/func/{name_of_function}",
            "headers":{}
        }
        if api_data.get('status') == 0:
            continue
        format = {
            "type": "function",
            "name": name_of_function,
            "description": api_data.get('description'),
            "properties": (
                api_data.get("fields", {}) if api_data.get("version") == 'v2' 
                else {item["variable_name"]: {
                    "description": item.get("description", ""), 
                    "enum": [] if(item.get("enum") == '') else item.get("enum", []),
                    "type": "string",
                    "parameter": {}
                } for item in api_data.get('fields',{})}
            ),
            "required": (
               api_data.get("required_params")
            )
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
    configuration.pop('tools', None)
    configuration['tools'] = tools
    service = service or (result.get('bridges', {}).get('service', '').lower())
    service = service.lower() if service else ""
    gpt_memory = result.get('bridges', {}).get('gpt_memory')
    db_apikeys = result.get('bridges', {}).get('apikeys')
    db_api_key = db_apikeys.get(service)
    apikey_object_id = result.get('bridges', {}).get('apikey_object_id')
    if not (apikey or db_api_key): 
        raise Exception('Could not find api key')
    apikey = apikey if apikey else Helper.decrypt(db_api_key)
    RTLayer = True if configuration and 'RTLayer' in configuration else False 
    bridge = result.get('bridges')
    template_content = await ConfigurationService.get_template_by_id(template_id) if template_id else None
    pre_tools = bridge.get('pre_tools', [])
    variables_path_bridge = bridge.get('variables_path', None)
    gpt_memory_context = bridge.get('gpt_memory_context')
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
        "variables": await updateVariablesWithTimeZone(variables,org_id)
    }
