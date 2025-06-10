from ..db_services.auth_service import save_auth_token_in_db, verify_auth_token
from fastapi.responses import JSONResponse


async def save_auth_token_in_db_controller(request):
    try:
        body = await request.json()
        client_id = body.get('client_id')
        redirection_url = body.get('redirection_url')
        org_id = request.state.profile.get("org",{}).get("id","")

        await save_auth_token_in_db(client_id, redirection_url, org_id)
        return JSONResponse({"success": True, "message": "Auth token saved successfully"})
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={"success": False, "message": f"Error saving auth token: {str(e)}"}
        )

async def verify_auth_token_controller(request):
    try:
        body = await request.json()
        client_id = body.get('client_id')
        redirection_url = body.get('redirection_url')
        result = await verify_auth_token(client_id, redirection_url)
        data = {
            'org_id' : result.get('org_id'),
            'client_id' : result.get('client_id'),
            'redirection_url' : result.get('redirection_url')
        }
        return JSONResponse({"success": True, "message": "Auth token verified successfully", "result": data})
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={"success": False, "message": f"Error saving auth token: {str(e)}"}
        )
