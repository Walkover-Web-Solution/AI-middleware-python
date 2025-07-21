import uuid
import hashlib
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from config import Config
from src.services.commonServices.generateToken import generateToken

async def login_public_user(request: Request):
    try:
        user_info = request.get('state', {}).get('profile', {}).get('user', {})
        user_id = user_info.get('id')
        user_email = user_info.get('email')
        is_public = not bool(user_email)

        # Attempt to use IP address as fallback user_id
        if not user_id:
            client_host = request.client.host if request.client else None
            if client_host:
                # Hash the IP to create a consistent but anonymized user ID
                user_id = hashlib.sha256(client_host.encode()).hexdigest()
            else:
                user_id = str(uuid.uuid4())  # Fallback to UUID if IP not available

        return {
            "token": generateToken({'userId': user_id, "userEmail": user_email, 'ispublic': is_public}, Config.PUBLIC_CHATBOT_TOKEN),
            "user_id": user_id
        }

    except HTTPException as http_error:
        raise http_error  # Re-raise HTTP exceptions for proper handling
    except Exception as error:
        return JSONResponse(status_code=400, content={'error': str(error)})
