from fastapi import Request, HTTPException
from src.services.utils.getConfiguration import getConfiguration
from src.services.utils.getOrchestratorConfiguration import getOrchestratorConfiguration
from globals import *
from src.configs.model_configuration import model_config_document

async def add_configuration_data_to_body(request: Request):

    try:
        body = await request.json()
        org_id = request.state.profile['org']['id']
        chatbotData = getattr(request.state, "chatbot", None)
        if chatbotData:
            body.update(chatbotData)
        # Check for orchestrator_id first
        orchestrator_id = body.get('orchestrator_id')
        
        if orchestrator_id:
            # Handle orchestrator configuration
            db_config = await getOrchestratorConfiguration( 
                orchestrator_id, 
                org_id, 
                body.get('variables', {}), 
                body.get('variables_path'),
                body.get('playground', False)
            )
        else:
            # Handle regular bridge configuration
            bridge_id = body.get('agent_id') or body.get("bridge_id") or request.path_params.get('bridge_id') or getattr(request.state, 'chatbot', {}).get('bridge_id', None)
            if chatbotData:
                del request.state.chatbot
            version_id = body.get('version_id') or request.path_params.get('version_id')
            db_config = await getConfiguration(
                body.get('configuration'), 
                body.get('service'), 
                bridge_id, 
                body.get('apikey'), 
                body.get('template_id'), 
                body.get('variables', {}), 
                org_id, 
                body.get('variables_path'), 
                version_id=version_id, 
                extra_tools=body.get('extra_tools', []), 
                built_in_tools=body.get('built_in_tools'),
                guardrails=body.get('guardrails'),
                web_search_filters=body.get('web_search_filters'),
                chatbot=body.get('chatbot', False)
            )
        if not db_config.get("success"):
                raise HTTPException(status_code=400, detail={"success": False, "error": db_config["error"]}) 
        body.update(db_config)
        if orchestrator_id:
            db_config['user'] = body.get('user')
            return db_config
        service = body.get("service")
        model = body.get("configuration").get('model')
        user = body.get("user")
        images = body.get("images") or []
        if user is None and len(images) == 0:
            raise HTTPException(status_code=400, detail={"success": False, "error": "User message is compulsory"})
        if not (service in model_config_document and model in model_config_document[service]):
            raise HTTPException(status_code=400, detail={"success": False, "error": "model or service does not exist!"})
        if model_config_document[service][model].get('org_id'):
            if model_config_document[service][model]['org_id'] != org_id:
                raise HTTPException(status_code=400, detail={"success": False, "error": "model or service does not exist!"})
            
        return db_config
    except HTTPException as he:
         raise he
    except Exception as e:
        logger.error(f"Error in get_data: {str(e)}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in getting data: "+ str(e)})
    

