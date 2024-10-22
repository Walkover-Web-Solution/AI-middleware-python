import aiohttp
import ssl
import certifi

async def fetch(url, method="GET", headers=None, params=None, json_body=None):
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession() as session:
        async with session.request(method=method, url=url, headers=headers, params=params, json=json_body, ssl=ssl_context) as response:
            # Extract the response body and headers
            if response.status >= 300:
                error_response = await response.text()
                raise  ValueError(error_response)
                
            response_data = await response.json()  # This gets the body as text (could also use .json() for JSON)
            response_headers = dict(response.headers)   # This gets the response headers
            return response_data, response_headers