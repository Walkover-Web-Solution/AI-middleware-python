import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
# from src.services.commonServices.generateToken import generateToken
# from src.configs.modelConfiguration import ModelsConfig

async def getConfiguration(configuration, service, bridge_id, apikey, template_id=None, variables = {}):
    RTLayer = False
    bridge = None
    result = await ConfigurationService.get_bridges(bridge_id)
    if not result['success']:
        return {
            'success': False,
            'error': "bridge_id does not exist"
        }
    db_configuration = result.get('bridges', {}).get('configuration', {})
    if configuration:
        db_configuration.update(configuration)
    configuration = db_configuration
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
        api_call = await ConfigurationService.get_api_call_by_names(pre_tools)

        if api_call.get('sucesss') is False: 
            raise Exception("Didn't find the pre_function")
        api_data =  api_call.get('apiCalls', [])
        api_data = api_data[0] if len(api_data) > 0 else {}
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


# def filter_data_of_bridge_on_the_base_of_ui(result, bridge_id, update=True):
    configuration = result.get('bridges', {}).get('configuration')
    type_ = configuration.get('type') if configuration and 'type' in configuration else ''
    model = configuration.get('model') if configuration and 'model' in configuration else ''
    modelname = model.replace("-", "_").replace(".", "_")
    modelfunc = ModelsConfig[modelname]
    model_config = modelfunc().configuration
    for key in model_config:
        if key in configuration:
            model_config[key]['default'] = configuration[key]
    
    custom_config = model_config
    for keys in configuration:
        if keys not in ["name", "type"]:
            custom_config[keys] = model_config.get(keys, configuration[keys])
    
    if configuration and 'max_tokens' in configuration and model_config and 'max_tokens' in model_config and configuration['max_tokens'] > model_config['max_tokens']['max']:
        configuration['max_tokens'] = model_config['max_tokens']['default']
    
    result['bridges']['apikey'] = Helper.decrypt(result['bridges']['apikey'])
    if update:
        embed_token = generate_token({
            'payload': {
                'org_id': os.getenv('ORG_ID'),
                'project_id': os.getenv('PROJECT_ID'),
                'user_id': bridge_id
            },
            'accessKey': os.getenv('ACCESS_KEY')
        })
        result['bridges']['embed_token'] = embed_token
    
    result['bridges']['type'] = type_
    result['bridges']['configuration'] = custom_config
