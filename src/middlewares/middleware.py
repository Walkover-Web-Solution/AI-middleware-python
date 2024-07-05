import jwt
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from config import Config

class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get('Authorization')
        if not token:
            return JSONResponse(status_code=498, content="invalid token")
        
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            if decoded_token:
                check_token = jwt.decode(token, Config.SecretKey, algorithms=["HS256"])
                if check_token:
                    check_token['org']['id'] = str(check_token['org']['id'])
                    request.state.profile = check_token
                    request.state.org_id = str(check_token.get('org', {}).get('id'))
                    response = await call_next(request)
                    return response
                
                return JSONResponse(status_code=404, content="unauthorized user")
            
            return JSONResponse(status_code=401, content="unauthorized user")
        
        except Exception as err:
            traceback.print_exc()
            print(f"middleware error => {err}")
            return JSONResponse(status_code=401, content="unauthorized user")