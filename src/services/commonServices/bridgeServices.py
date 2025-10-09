from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.services.prebuilt_prompt_service import get_specific_prebuilt_prompt_service
from src.db_services.ConfigurationServices import get_bridges, get_bridges_with_tools
from src.configs.constant import bridge_ids
from src.services.utils.ai_call_util import call_ai_middleware
from globals import *
    

async def optimize_prompt_controller(request : Request, bridge_id: str):
    try:
        body = await request.json()
        version_id = body.get('version_id')
        variables = {
          "query": body.get('query') or ""
        }
        thread_id = body.get('thread_id') or None
        org_id = request.state.profile.get("org",{}).get("id","")
        result = await get_bridges(bridge_id, org_id, version_id)
        bridge = result.get('bridges')
        prompt = bridge.get('configuration',{}).get('prompt',"")
        result = ""
        configuration = None
        updated_prompt = await get_specific_prebuilt_prompt_service(org_id, 'optimze_prompt')
        if updated_prompt and updated_prompt.get('optimze_prompt'):
            configuration = {"prompt": updated_prompt['optimze_prompt']}
        result = await call_ai_middleware(prompt, variables=variables, configuration=configuration, thread_id=thread_id, bridge_id = bridge_ids['optimze_prompt'], response_type='text')
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Prompt optimized successfully",
            "result" : result
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in optimizing prompt: "+ str(e)})
    
async def generate_summary(request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org",{}).get("id","")
        version_id = body.get('version_id')
        get_version_data = (await get_bridges_with_tools(None, org_id, version_id)).get("bridges")
        if not get_version_data:
            return {
                "success": False,
                "error": "Version data not found"
            }
        tools = {tool['endpoint_name']: tool['description'] for tool in get_version_data.get('apiCalls', {}).values()}
        system_prompt = get_version_data.get('configuration',{}).get('prompt')
        if tools:
            system_prompt += f'Available tool calls :-  {tools}'
        variables = {'prompt' : system_prompt}
        user = "generate summary from the user message provided in system prompt"
        configuration = None
        updated_prompt = await get_specific_prebuilt_prompt_service(org_id, 'generate_summary')
        if updated_prompt and updated_prompt.get('generate_summary'):
            configuration = {"prompt": updated_prompt['generate_summary']}
        summary = await call_ai_middleware(user, bridge_id = bridge_ids['generate_summary'], configuration=configuration, response_type='text', variables = variables)
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Summary generated successfully",
            "result" : summary
        })
            
    except Exception as err:
        logger.error("Error calling function generate_summary =>", err)
async def function_agrs_using_ai(request):
    try:
        body = await request.json()
        data = body.get('example_json')
        user = f"geneate the json using the example json data : {data}"
        json = await call_ai_middleware(user, bridge_id = bridge_ids['function_agrs_using_ai'])
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "json generated successfully",
            "result" : json
        })
            
    except Exception as err:
        logger.error("Error calling function function_agrs_using_ai =>", err)
    