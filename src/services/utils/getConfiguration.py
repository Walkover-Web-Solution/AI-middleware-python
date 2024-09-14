import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
from bson import ObjectId
from models.mongo_connection import db
apiCallModel = db['apicalls']

# from src.services.commonServices.generateToken import generateToken
# from src.configs.modelConfiguration import ModelsConfig

async def getConfiguration(configuration, service, bridge_id, apikey, template_id=None, variables = {}, org_id=""):
    RTLayer = False
    bridge = None
    result = await ConfigurationService.get_bridges_with_tools(bridge_id, org_id)
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
    for key, api_data in result.get('bridges', {}).get('apiCalls', {}).items():
        # if status is paused then only don't include it in tools
        if api_data.get('status') == 0:
            continue
        format = {
            "type": "function",
            "name": api_data.get("function_name", api_data.get("endpoint")),
            "description": api_data.get("description", api_data.get("short_description")),
            "properties": { field: { "type": "string" } for field in api_data.get("required_params", api_data.get("required_fields"))  },
            "required": api_data.get("required_params", api_data.get("required_fields"))
        }
        tools.append(format)

    configuration.pop('tools', None)
    configuration['tools'] = tools

    service = service or (result.get('bridges', {}).get('service', '').lower())
    db_api_key = result.get('bridges', {}).get('apikey')
    if not (apikey or db_api_key): 
        raise Exception('Could not find api key')
    apikey = apikey if apikey else Helper.decrypt(db_api_key)
    RTLayer = True if configuration and 'RTLayer' in configuration else False 
    bridge = result.get('bridges')
    service = service.lower() if service else ""
    template_content = await ConfigurationService.get_template_by_id(template_id) if template_id else None
    pre_tools = bridge.get('pre_tools', [])
    if len(pre_tools)>0:
        api_data = apiCallModel.find_one({"_id": ObjectId( pre_tools[0]), "org_id": org_id})

        if api_data is None: 
            raise Exception("Didn't find the pre_function")
        pre_function_code = api_data.get('code', '')
        required_params = api_data.get('required_params', [])
        args = {}
        for param in required_params:
            if param in variables :
                args[param] = variables[param]
        
    return {
        'success': True,
        'configuration': configuration,
        'bridge': bridge,
        'pre_tools': {'pre_function_code': pre_function_code, 'args': args} if len(pre_tools)>0 else None,
        'service': service,
        'apikey': apikey,
        'RTLayer': RTLayer,
        'template': template_content.get('template') if template_content else None
    }
