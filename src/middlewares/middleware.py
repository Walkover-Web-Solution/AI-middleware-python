import jwt
from fastapi import Request, HTTPException
import traceback
from config import Config
from src.services.utils.apiservice import fetch
from src.services.utils.helper import Helper
from src.services.proxy.Proxyservice import (
    get_proxy_details_by_token,
    validate_proxy_pauthkey,
)
from src.services.utils.time import Timer
from globals import *
from bson import ObjectId
from src.db_services.ConfigurationServices import configurationModel

async def make_data_if_proxy_token_given(req):
    proxy_auth_token = req.headers.get('proxy_auth_token')
    proxy_pauth_token = req.headers.get('pauthkey')

    if proxy_auth_token:
        response_data = await get_proxy_details_by_token(proxy_auth_token)
        
        # Get current company ID
        current_company_id = response_data['data'][0]['currentCompany']['id']
        
        # Find role_name from c_companies matching currentCompany.id
        role_name = None
        c_companies = response_data['data'][0].get('c_companies', [])
        for company in c_companies:
            if company.get('id') == current_company_id:
                role_name = company.get('role_name')
                break
        
        data = {
            'ip': "9.255.0.55",
            'user': {
                'id': response_data['data'][0]['id'],
                'name': response_data['data'][0]['name'],
                'is_embedUser': response_data['data'][0]['meta'].get('type') == 'embed',
                'folder_id': response_data['data'][0]['meta'].get('folder_id', None),
                'email': response_data['data'][0]['email'],
                'role_name': role_name
            },
            'org': {
                'id': response_data['data'][0]['currentCompany']['id'],
                'name': response_data['data'][0]['currentCompany']['name']
            }
        }
        return data

    if proxy_pauth_token:
        validation_response = await validate_proxy_pauthkey(proxy_pauth_token)
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
            print(f"check_token => {check_token}")
            if check_token:
                check_token['org']['id'] = str(check_token['org']['id'])
                request.state.profile = check_token
                request.state.org_id = str(check_token.get('org', {}).get('id'))
                meta = check_token['user'].get('meta', {})
                if isinstance(meta, dict):
                    request.state.embed = meta.get('type', False) == 'embed' or False
                else:
                    request.state.embed = False
                request.state.folder_id = check_token.get('extraDetails', {}).get('folder_id', None)
                request.state.user_id = str(check_token['user'].get('id'))
                request.state.role_name = check_token.get('user', {}).get('role_name')
                return 
            
            raise HTTPException(status_code=404, detail="unauthorized user")        
        except Exception as err:
            traceback.print_exc()
            logger.error(f"middleware error => {str(err)}")
            raise HTTPException(status_code=401, detail="unauthorized user")

async def get_agent_access_role(user_id: str, org_id: str, bridge_id: str, original_role_name: str = None) -> str:
    """
    Helper function to get access role for a specific bridge.
    
    Logic:
    1. If original_role_name is 'owner' -> return 'owner' (no DB check needed)
    2. If 'users' array exists in configuration and contains user_id -> return 'member'
    3. If 'users' array doesn't exist -> return original_role_name
    4. If 'users' array exists but doesn't contain user_id -> return 'viewer'
    
    Returns:
        str: The access role ('owner', 'member', 'viewer', or original_role_name)
    """
    try:
        # If user is owner, return 'owner' immediately without checking DB
        if original_role_name == 'owner':
            return 'owner'
        
        if not user_id:
            # If no user_id, return original role_name
            return original_role_name
        
        # Query configuration collection for the bridge
        try:
            bridge_doc = await configurationModel.find_one(
                {'_id': ObjectId(bridge_id), 'org_id': org_id},
                {'users': 1}
            )
        except Exception as e:
            logger.error(f"Error querying configuration for bridge {bridge_id}: {str(e)}")
            # If query fails, return original role_name
            return original_role_name
        
        if bridge_doc is None:
            # Bridge not found, return original role_name
            return original_role_name
        
        # Check if 'users' key exists
        users_array = bridge_doc.get('users')
        
        if users_array is None:
            # 'users' key doesn't exist, return original role_name
            return original_role_name
        
        # Ensure users_array is a list
        if not isinstance(users_array, list):
            # If 'users' exists but is not a list, return original role_name
            return original_role_name
        
        # Convert user_id to string for comparison (users array might contain strings or integers)
        user_id_str = str(user_id)
        
        # Check if user_id is in the users array
        # Handle both string and integer comparisons
        user_found = any(str(u) == user_id_str for u in users_array)
        
        if user_found:
            # User found in array, return 'member'
            return 'member'
        else:
            # User not found in array, return 'viewer'
            return 'viewer'
            
    except Exception as err:
        logger.error(f"Error in get_agent_access_role: {str(err)}")
        # On error, return original role_name
        return original_role_name

async def check_agent_access_middleware(request: Request, bridge_id: str):
    """
    Middleware to check and update user's role_name based on agent-specific permissions.
    Stores the result in request.state.access_role.
    """
    try:
        user_id = request.state.user_id
        original_role_name = request.state.role_name
        org_id = request.state.org_id
        
        access_role = await get_agent_access_role(user_id, org_id, bridge_id, original_role_name)
        request.state.access_role = access_role
            
    except Exception as err:
        logger.error(f"Error in check_agent_access_middleware: {str(err)}")
        # On error, fallback to original role_name
        request.state.access_role = getattr(request.state, 'role_name', None)
