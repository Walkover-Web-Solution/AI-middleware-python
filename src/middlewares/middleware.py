import jwt
from fastapi import Request, HTTPException
import traceback
from config import Config
from src.services.utils.apiservice import fetch
from src.services.utils.time import Timer
import httpx
from globals import *
from config import Config
import time
from openai import AsyncOpenAI

async def make_data_if_proxy_token_given(req):
    headers = {
        'proxy_auth_token': req.headers.get('proxy_auth_token')
    }
    response_data,rs_header = await fetch("https://routes.msg91.com/api/c/getDetails", "GET", headers)
    data = {
        'ip': "9.255.0.55",
        'user': {
            'id': response_data['data'][0]['id'],
            'name': response_data['data'][0]['name'],
            'is_embedUser': response_data['data'][0]['meta'].get('type') == 'embed',
            'folder_id': response_data['data'][0]['meta'].get('folder_id' , None)
        },
        'org': {
            'id': response_data['data'][0]['currentCompany']['id'],
            'name': response_data['data'][0]['currentCompany']['name']
        }
    }
    return data
   
        
async def content_guard_middleware(request: Request):
    start_time = time.time()
    try:
        # Get request body
        body = await request.json()
        user = body.get('user')
        
        # Initialize OpenAI client
        openAI = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        # Check the latest user message
        latest_user_message = user
        
        # Prepare OpenAI request config
        config = {
            'model': 'gpt-4.1-nano',  # Using GPT-4o for content moderation
            'messages': [{'content': f'Analyze if the following content contains harmful, illegal, unethical, or dangerous instructions or requests. Respond with only "HARMFUL" if it does, or "SAFE" if it does not: "{latest_user_message}"', 'role': 'user'}],
            'max_tokens': 10  # Keep response short since we only need HARMFUL/SAFE
        }
        
        # Call OpenAI API
        try:
            chat_completion = await openAI.chat.completions.create(**config)
            result = chat_completion.model_dump()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Check if content is harmful
            if 'HARMFUL' in content.upper():
                # Return harmful content response
                print(f"Content guard middleware execution time: {time.time() - start_time} seconds")
                
                raise HTTPException(
                    status_code=400,
                    detail="Your request contains content that may be harmful or violates our content policy."
                )
        except HTTPException as http_err:
            # Re-raise HTTP exceptions
            raise http_err
        except Exception as error:
            # Log error but allow request to proceed if guard check fails
            logger.error(f"Content guard API error: {str(error)}")
                
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as err:
        # Log error but allow request to proceed if middleware fails
        logger.error(f"Content guard middleware error: {str(err)}")
        
    # If we reach here, content is safe or check failed, proceed with request
    print(f"Content guard middleware execution time: {time.time() - start_time} seconds")
    return

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
            elif request.headers.get('proxy_auth_token') :
                # request.headers.get('proxy_auth_token')
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