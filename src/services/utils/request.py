import httpx
import json 

async def send_request(url, data, method, header):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, json=data, headers=header)
            return response
    except httpx.RequestError as error:
        print("send_request error=>", error)
        return None
    
async def send_message(cred, data ):
    try:
        async with httpx.AsyncClient() as client :
            response = await client.post(url=f"https://api.rtlayer.com/message?apiKey={cred['apikey']}", data = {
                **cred,
                'message' : json.dumps(data)
            })
            return response
    except httpx.RequestError as error:
        print('send message error=>', error)