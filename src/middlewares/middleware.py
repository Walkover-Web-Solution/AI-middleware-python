import jwt
from fastapi import Request, HTTPException
import traceback
from config import Config
from src.services.utils.apiservice import fetch
from src.services.utils.helper import Helper
from src.services.utils.time import Timer
from globals import *

async def make_data_if_proxy_token_given(req):
    proxy_auth_token = req.headers.get('proxy_auth_token')
    proxy_pauth_token = req.headers.get('pauthkey')

    if proxy_auth_token:
        headers = {
            'proxy_auth_token': proxy_auth_token
        }
        response_data, rs_header = await fetch("https://routes.msg91.com/api/c/getDetails", "GET", headers)
        data = {
            'ip': "9.255.0.55",
            'user': {
                'id': response_data['data'][0]['id'],
                'name': response_data['data'][0]['name'],
                'is_embedUser': response_data['data'][0]['meta'].get('type') == 'embed',
                'folder_id': response_data['data'][0]['meta'].get('folder_id', None),
                'email': response_data['data'][0]['email']
            },
            'org': {
                'id': response_data['data'][0]['currentCompany']['id'],
                'name': response_data['data'][0]['currentCompany']['name']
            }
        }
        return data

    if proxy_pauth_token:
        validation_response = await Helper.validate_proxy_pauthkey(proxy_pauth_token)
        if validation_response.get('hasError') or validation_response.get('status') != 'success':
            raise HTTPException(status_code=401, detail="invalid pauthkey")

        proxy_data = validation_response.get('data', {})
        company = proxy_data.get('company') or {}
        authkey_info = proxy_data.get('authkey') or {}
        company_id = company.get('id')
        authkey_id = authkey_info.get('id')
        user_name = authkey_info.get('name') or company.get('name')

        if company_id is None:
            raise HTTPException(status_code=401, detail="invalid pauthkey")

        return {
            'ip': "9.255.0.55",
            'user': {
                'id': str(authkey_id if authkey_id is not None else company_id),
                'name': user_name,
                'is_embedUser': False,
                'folder_id': None,
                'email': None
            },
            'org': {
                'id': str(company_id),
                'name': company.get('name')
            },
            'authkey': authkey_info,
            'extraDetails': {
                'proxy_auth_type': 'pauthkey'
            }
        }

    raise HTTPException(status_code=401, detail="missing proxy credentials")

async def jwt_middleware(request: Request):
        try:
            timer_obj = Timer()
            timer_obj.start()
            request.state.timer = timer_obj.getTime()
            # request.state.timer = timer
            check_token = False
            if request.headers.get('Authorization') :
                token = request.headers.get('Authorization')
                if not token:
                    raise HTTPException(status_code=498, detail="invalid token")
                check_token = jwt.decode(token, Config.SecretKey, algorithms=["HS256"])
            elif request.headers.get('proxy_auth_token') or request.headers.get('pauthkey'):
                check_token = await make_data_if_proxy_token_given(request)

            if check_token:
                check_token['org']['id'] = str(check_token['org']['id'])
                request.state.profile = check_token
                request.state.org_id = str(check_token.get('org', {}).get('id'))
                if isinstance(check_token['user'].get('meta'), str):
                    request.state.embed = False
                else:
                    request.state.embed = check_token['user'].get('meta', {}).get('type', False) == 'embed' or False
                request.state.folder_id = check_token.get('extraDetails', {}).get('folder_id', None)
                request.state.user_id = check_token['user'].get('id')
                return 
            
            raise HTTPException(status_code=404, detail="unauthorized user")        
        except Exception as err:
            traceback.print_exc()
            logger.error(f"middleware error => {str(err)}")
            raise HTTPException(status_code=401, detail="unauthorized user")
