import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
# from src.services.commonServices.generateToken import generateToken
# from src.configs.modelConfiguration import ModelsConfig

async def getConfiguration(configuration, service, bridge_id, api_key, template_id=None):
    RTLayer = False
    bridge = None
    result = {} or await ConfigurationService.get_bridges(bridge_id)
    if not result['success']:
        return {
            'success': False,
            'error': "bridge_id does not exist"
        }
    configuration = configuration if configuration else result.get('bridges', {}).get('configuration')
    service = service or (result.get('bridges', {}).get('service', '').lower())
    api_key = api_key if api_key else Helper.decrypt(result.get('bridges', {}).get('apikey'))
    RTLayer = True if configuration and 'RTLayer' in configuration else False 
    bridge = result.get('bridges')
    service = service.lower() if service else ""
    # template_content = await ConfigurationService.get_template_by_id(template_id) if template_id else None
    template_content = None
    return {
        'success': True,
        'configuration': configuration,
        'bridge': bridge,
        'service': service,
        'apikey': api_key,
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
