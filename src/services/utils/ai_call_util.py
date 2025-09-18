from .apiservice import fetch
import json
import jwt

def generate_token(payload, accesskey):
        return jwt.encode(payload, accesskey)

async def call_ai_middleware(user, bridge_id, variables = {}, configuration = None, response_type = None, thread_id = None):
    request_body = {
        "user": user,
        "bridge_id": bridge_id,
        "variables": variables
    }
    if response_type is not None:
        request_body["response_type"] = response_type
    
    if configuration is not None:
        request_body["configuration"] = configuration
    
    if thread_id is not None:
        request_body["thread_id"] = thread_id
    
    response, rs_headers = await fetch(
        f"https://api.gtwy.ai/api/v2/model/chat/completion",
        "POST",
        {
            "pauthkey": "1b13a7a038ce616635899a239771044c",
            "Content-Type": "application/json"
        },
        None,
        request_body
    )
    if not response.get('success', True):
        raise Exception(response.get('message', 'Unknown error'))
    result = response.get('response', {}).get('data', {}).get('content', "")
    if response_type is None:
        result = json.loads(result)
    return result

async def call_gtwy_agent(args):
    try:
        # Import inside function to avoid circular imports
        from src.services.commonServices.common import chat
        from src.services.utils.getConfiguration import getConfiguration
        request_body = {}
        # Add thread_id and sub_thread_id if provided
        if args.get('thread_id'):
            request_body["thread_id"] = args.get('thread_id')
        if args.get('sub_thread_id'):
            request_body["sub_thread_id"] = args.get('sub_thread_id')
        
        org_id = args.get('org_id')
        bridge_id = args.get('bridge_id')
        version_id = args.get('version_id')
        user_message = args.get('user')
        variables = args.get('variables') or {}
        
        # Step 1: Update request body with core data
        request_body.update({
            "user": user_message,
            "bridge_id": bridge_id,
            "variables": variables
        })
        # If version_id is provided, include it in the request body early
        if version_id:
            request_body["version_id"] = version_id
        
        # Step 2: Call the configuration middleware to enrich the data
        # This simulates what add_configuration_data_to_body does
        db_config = await getConfiguration(
            configuration=request_body.get('configuration'),
            service=request_body.get('service'),
            bridge_id=bridge_id,
            apikey=request_body.get('apikey'),
            template_id=request_body.get('template_id'),
            variables=variables,
            org_id=org_id,
            variables_path=request_body.get('variables_path'),
            version_id=version_id,
            extra_tools=request_body.get('extra_tools', []),
            built_in_tools=request_body.get('built_in_tools')
        )
        db_config['org_id'] = org_id
        
        if not db_config.get("success"):
            raise Exception(db_config.get("error", "Configuration fetch failed"))
        
        # Step 3: Update request body with configuration data (like middleware does)
        request_body.update(db_config)
        # Prefer version_id over agent_id when provided: ensure version_id is set and remove agent_id
        if version_id:
            request_body["version_id"] = version_id
            request_body.pop("agent_id", None)
            request_body.pop("bridge_id", None)
        
        # Step 4: Create data structure for chat function
        data_to_send = {
            "body": request_body
        }
        
        # Step 5: Call the chat function directly
        response = await chat(data_to_send)
        
        # Handle JSONResponse object - extract the actual response data
        if hasattr(response, 'body'):
            # For JSONResponse, get the body content
            import json
            response_data = json.loads(response.body.decode('utf-8'))
        else:
            # If it's already a dict, use it directly
            response_data = response
        
        if not response_data.get('success', True):
            raise Exception(response_data.get('message', 'Unknown error'))
        
        data_section = response_data.get('response', {}).get('data', {})
        result = data_section.get('content', "")
        
        # Check for image URLs and include them if present
        image_urls = data_section.get('image_urls')
        
        try:
            parsed_result = json.loads(result) if result else {}
        except json.JSONDecodeError:
            parsed_result = {"data": result}
        
        # Add image URLs to the result if they exist
        if image_urls:
            if isinstance(parsed_result, dict):
                parsed_result['image_urls'] = image_urls
            else:
                parsed_result = {"data": parsed_result, "image_urls": image_urls}
        
        return parsed_result
            
    except Exception as e:
        raise Exception(f"Error in call_gtwy_agent: {str(e)}")
