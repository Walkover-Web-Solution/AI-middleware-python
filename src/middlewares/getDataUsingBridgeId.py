from fastapi import Request
from fastapi.responses import JSONResponse
from ..services.utils.getConfiguration import getConfiguration


async def get_data(request: Request):

    try:
        body = await request.json()
        bridge_id = body.get("bridge_id") or request.path_params.get('bridge_id')
        if(hasattr(request.state, 'body')):
                body.update(request.state.body)
        db_config = await getConfiguration(body.get('configuration'), body.get('service'), bridge_id, body.get('apikey'), body.get('template_id'))
        if not db_config.get("success"):
                return JSONResponse(status_code=400, content={"success": False, "error": db_config["error"]}) 
        body.update(db_config)
        request.state.body = body   
        
        return db_config
    except Exception as e:
        print("Error in get_data: ", e)
        return JSONResponse(status_code=400, content={"success": False, "error": "Error in get_data: "+ str(e)})


