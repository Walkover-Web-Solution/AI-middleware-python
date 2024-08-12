import jwt
from fastapi import Request, HTTPException
import traceback
from config import Config

import requests

async def make_data_if_proxy_token_given(req):
    headers = {
        'proxy_auth_token': req.headers.get('proxy_auth_token')
    }
    response = requests.get("https://routes.msg91.com/api/c/getDetails", headers=headers)

    if response.status_code != 200 or not response.json():
        raise Exception("Invalid token")

    response_data = response.json()
    data = {
        'ip': "9.255.0.55",
        'user': {
            'id': response_data['data'][0]['id'],
            'name': response_data['data'][0]['name']
        },
        'org': {
            'id': response_data['data'][0]['c_companies'][0]['id'],
            'name': response_data['data'][0]['c_companies'][0]['name']
        }
    }
    return data
   
        
async def jwt_middleware(request: Request):
        try:
            if request.headers.get('proxy_auth_token') :
                check_token = await make_data_if_proxy_token_given(request)
            else :
                token = request.headers.get('Authorization')
                if not token:
                    raise HTTPException(status_code=498, detail="invalid token")
                check_token = jwt.decode(token, Config.SecretKey, algorithms=["HS256"])

            if check_token:
                check_token['org']['id'] = str(check_token['org']['id'])
                request.state.profile = check_token
                request.state.org_id = str(check_token.get('org', {}).get('id'))
                return 
            
            raise HTTPException(status_code=404, detail="unauthorized user")        
        except Exception as err:
            traceback.print_exc()
            print(f"middleware error => {err}")
            raise HTTPException(status_code=401, detail="unauthorized user")