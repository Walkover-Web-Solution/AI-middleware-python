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
    
async def send_message(data, channel=None):
    try:
        async with httpx.AsyncClient() as client :
            response = await client.post(url='https://api.rtlayer.com/message?apiKey=hRzOZCelBrcFEIbojtst', data = {
                'message' : json.dumps(data),
                'channel' : channel
            })
            return response
    except httpx.RequestError as error:
        print('send message error=>', error)