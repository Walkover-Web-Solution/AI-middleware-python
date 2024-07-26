from fastapi import HTTPException, status
from src.services.utils.helper import Helper
from src.db_services.ConfigurationServices import create_bridge, get_bridges, update_tools_calls

async def create_bridges(bridges):
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

# todo :: change the way tool calls are getting saved in the db
async def get_and_update(api_object_id, bridge_id, org_id, open_api_format, function_name, required_params, status="add"):
    try:
        model_config = await get_bridges(bridge_id)
        tools_call = model_config.get('bridges', {}).get('configuration', {}).get('tools', [])
        api_endpoints = model_config.get('bridges', {}).get('api_endpoints', [])
        api_call = model_config.get('bridges', {}).get('api_call', {})

        if function_name not in api_call:
            api_endpoints.append(function_name)

        updated_tools_call = [tool for tool in tools_call if tool['function']['name'] != function_name]

        if status == "add":
            updated_tools_call.append(open_api_format)
            api_call[function_name] = {
                "apiObjectID": api_object_id,
                "requiredParams": required_params,
                "functioName": function_name
            }

        if status == "delete":
            api_endpoints = [item for item in api_endpoints if item != function_name]
            if function_name in api_call:
                del api_call[function_name]

        tools_call = updated_tools_call
        configuration = {
            "tools": tools_call
        }

        new_configuration = Helper.update_configuration(model_config['bridges']['configuration'], configuration)
        result = await update_tools_calls(bridge_id, org_id, new_configuration, api_endpoints, api_call)
        result['tools_call'] = tools_call
        return result

    except Exception as error:
        print(f"error: {error}")
        return {
            "success": False,
            "error": "something went wrong!!"
        }