from .request import send_request, send_message

class ResponseSender:
    @staticmethod
    async def sendResponse(response_format, data, success = False):
        data_to_send = {
            'data' if success else 'error': data,
            'success': success
        }

        match response_format['type']:
            case 'rtlayer' : 
                return await send_message(cred = response_format['cred'], data=data_to_send)
            case 'webhook':
                return await send_request(**response_format['cred'], method='POST', data=data_to_send)

__all__ = ["ResponseSender"]
