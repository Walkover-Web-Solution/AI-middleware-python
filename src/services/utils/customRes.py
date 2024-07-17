from .request import send_request, send_message

class ResponseSender:
    @staticmethod
    async def sendResponse(rtl_layer=None, webhook=None, data=None, req_body={}, headers=None):
        if rtl_layer:
            print('req body', req_body)
            await send_message(data, req_body['rtlOptions'])
        if webhook:
            print("webhook 1st entry")
            await send_request(webhook, {**req_body, **data}, 'POST', headers)
        return

__all__ = ["ResponseSender"]
