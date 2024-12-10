from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import json
class ResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            response_data = b""
            async for chunk in response.body_iterator:
                response_data += chunk
            response_data = json.loads(response_data.decode("utf-8"))
            if response_data:
                formatted_response = {
                    "status": 200,
                    "success": True,
                    "message": "Request processed successfully",
                    "data": response_data or {}
                }
                return JSONResponse(content=formatted_response, status_code=200)

            return response

        except HTTPException as http_exc:
            print("HTTP Error")
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"message": http_exc.detail, "data": {}},
            )
        except ValueError as ve:
            print("HTTP_422")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"message": str(ve), "data": {}},
            )
        except Exception:
            print("Default HTTP_400")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Something went wrong, try again later", "data": {}},
            )