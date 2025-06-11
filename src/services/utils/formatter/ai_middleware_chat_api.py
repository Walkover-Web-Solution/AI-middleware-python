import json
from src.configs.constant import bridge_ids
from ..ai_call_util import call_ai_middleware
from globals import *

async def structured_output_optimizer(request):
    try:
        body = await request.json()
        variables = {'json_schema': body.get('json_schema')}
        user = 'create the json shcmea accroding to the dummy json explained in system prompt.'
        result = await call_ai_middleware(user, bridge_id = bridge_ids['structured_output_optimizer'], variables = variables)
        return result
    except Exception as err:
        logger.error("Error calling function structured_output_optimizer=>", err)
        return None