from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
class ResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Get the original response
        response = await call_next(request)

        response_data = getattr(request.state, "response", None)
        status_code = getattr(request.state, "statusCode", None)
        # Read the response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        response_body = json.loads(response_body.decode("utf-8"))
        print(response_body)
        # If response_data exists, format it
        if response_data:
            success = response_data.get("success", status_code == 200)
            message = response_data.get("message", "Request processed successfully")
            data = response_data.get("data", {})

            formatted_response = {
                "status": status_code,
                "success": success,
                "message": message,
                "data": data
            }

            return JSONResponse(content=formatted_response, status_code=status_code)

        return response
