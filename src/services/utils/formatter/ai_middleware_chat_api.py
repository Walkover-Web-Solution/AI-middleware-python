import json
from src.services.prebuilt_prompt_service import get_specific_prebuilt_prompt_service
from src.configs.constant import bridge_ids
from ..ai_call_util import call_ai_middleware
from globals import *

async def structured_output_optimizer(request):
    try:
        body = await request.json()
        variables = {'json_schema': body.get('json_schema'),'query':body.get('query')}
        thread_id = body.get('thread_id') or None
        org_id = request.state.profile.get("org",{}).get("id","")
        user = 'create the json shcmea accroding to the dummy json explained in system prompt.'
        configuration = None
        updated_prompt = await get_specific_prebuilt_prompt_service(org_id, 'structured_output_optimizer')
        if updated_prompt and updated_prompt.get('structured_output_optimizer'):
            configuration = {"prompt": updated_prompt['structured_output_optimizer']}
        result = await call_ai_middleware(user, bridge_id = bridge_ids['structured_output_optimizer'],configuration = configuration, variables = variables, thread_id=thread_id)
        return result
    except Exception as err:
        logger.error("Error calling function structured_output_optimizer=>", err)
        return None