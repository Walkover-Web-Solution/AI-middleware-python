from fastapi import HTTPException, status
# from src.db_services.ConfigurationServices import get_bridges_by_slug_name_and_name
from src.db_services.ConfigurationServices import create_bridge, get_bridge_by_id, get_all_bridges_in_org
from src.configs.modelConfiguration import ModelsConfig as model_configuration



async def create_bridge(bridges):
    try:
        service = bridges.get('service')
        model = bridges.get('model')
        name = bridges.get('name')
        slugName = bridges.get('slugName')
        configuration = getattr(model_configuration,model,None)
        print(configuration,"hello configuration")
        # result = await create_bridge({
        #     "configuration": configuration,
        #     "name": name,
        #     "slugName": slugName,
        #     "service": service,
        # })
        return {
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body!")    

async def duplicate_create_bridges(bridges):
    try:

        org_id = bridges.get('org_id')
        service = bridges.get('service') 
        bridgeType = bridges.get('bridgeType')
        name = bridges.get('name')
        configuration = bridges.get('configuration') 
        apikey = bridges.get('apikey') 
        created_at = bridges.get('created_at') 
        api_call  = bridges.get('api_call') 
        api_endpoints = bridges.get('api_endpoints')
        is_api_call = bridges.get('is_api_call')
        slugName = bridges.get('slugName') 
        responseIds = bridges.get('responseIds')
        responseRef = bridges.get('responseRef')
        defaultQuestions = bridges.get('defaultQuestions')
        actions= bridges.get('actions')

        # bridge_data = await get_bridges_by_slug_name_and_name(slugName,name, org_id)
        # if bridge_data.get("success") and bridge_data.get("bridges"):
        #     if bridge_data["bridges"]["name"] == configuration['name']:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bridge name already exists! Please choose a unique one.")
        #     if bridge_data["bridges"]["slugName"] == configuration['slugName']:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug name already exists! Please choose a unique one.")

        result = await create_bridge({
            "configuration": configuration,
            "org_id": org_id,
            "name": name,
            "slugName": slugName,
            "service": service,
            "apikey": apikey,
            "bridgeType": bridgeType,
            "created_at": created_at,
            "api_call" : api_call,
            "api_endpoints": api_endpoints,
            "is_api_call" : is_api_call,
            "responseIds" : responseIds,
            "responseRef" : responseRef,
            "defaultQuestions" : defaultQuestions,
            "actions" : actions
        })

        if result.get("success"):
            res = result.get('bridge')
            return res

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)

    except HTTPException as e:
        raise e
    except Exception as error:
        print(f"common error=> {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An unexpected error occurred while creating the bridge. Please try again later.")

async def get_bridge(request,bridge_id: str):
    try:
        org_id = request.state.profile['org']['id']
        bridge = await get_bridge_by_id(org_id,bridge_id)
        return bridge
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body!")

async def get_all_bridges(request):
    try:
        org_id = request.state.profile['org']['id']
        bridges = await get_all_bridges_in_org(org_id)
        return bridges
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))