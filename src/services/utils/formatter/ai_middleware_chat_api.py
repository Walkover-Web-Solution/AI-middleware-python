from ..apiservice import fetch

async def structured_output_optimizer(request):
    try:
        body = await request.json()
        variables = {'json_schema': body.get('json_schema')}
        
        response, rs_headers = await fetch(
            f"https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion",
            "POST",
            {
                "pauthkey": "1b13a7a038ce616635899a239771044c",
                "Content-Type": "application/json"
            },
            None,
            {
                "user": "create the json shcmea accroding to the dummy json stored in system prompt",
                "bridge_id": "67766c4eec020b944b3e0670",
                "variables": variables
            }
        )
        if not response.get('success', True):
            raise Exception(response.get('message', 'Unknown error'))
        return response.get('response', {}).get('data', {}).get('content', "")
    except Exception as err:
        print("Error calling function=>", err)
        return None