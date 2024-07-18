import jwt
from fastapi import Request, HTTPException
import traceback
from config import Config
   
        
async def jwt_middleware(request: Request):
        token = request.headers.get('Authorization')
        if not token:
            raise HTTPException(status_code=498, detail="invalid token")
        
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            if decoded_token:
                check_token = jwt.decode(token, Config.SecretKey, algorithms=["HS256"])
                if check_token:
                    check_token['org']['id'] = str(check_token['org']['id'])
                    request.state.profile = check_token
                    request.state.org_id = str(check_token.get('org', {}).get('id'))
                    return
                
                raise HTTPException(status_code=404, detail="unauthorized user")
            
            raise HTTPException(status_code=401, detail="unauthorized user")
        
        except Exception as err:
            traceback.print_exc()
            print(f"middleware error => {err}")
            raise HTTPException(status_code=401, detail="unauthorized user")