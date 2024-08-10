from ..services.cache_service import find_in_cache, store_in_cache, verify_ttl
import json
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

def get_nested_value(obj, path):
    """Extract nested value from the request object."""
    for key in path.split('.'):
        if hasattr(obj, key):
            obj = getattr(obj, key)
        elif isinstance(obj, dict) and key in obj:
            obj = obj[key]
        else:
            return None
    return obj

async def rate_limit(request: Request, key_path: str, points: int = 40, ttl: int = 60):
    key = get_nested_value(request.state, key_path)
    if not key:
        raise HTTPException(status_code=400, detail="Invalid key path or key not found in request")

    redis_key = f"rate-limit:{key}"
    record = await find_in_cache(redis_key)

    if record:
        ttl = await verify_ttl(redis_key)
        data = json.loads(record)
        count = data['count']
        if count >= points:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={"Retry-After": str(ttl)}
            )
        data['count'] += 1
    else:
        data = {'count': 1}

    await store_in_cache(redis_key, data, ttl)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, key_path: str, points: int = 40, ttl: int = 60):
        super().__init__(app)
        self.key_path = key_path
        self.points = points
        self.ttl = ttl

    async def dispatch(self, request: Request, call_next):
        try:
            await rate_limit(request, self.key_path, self.points, self.ttl)
            return await call_next(request)
        except HTTPException as error:
            return Response(status_code=error.status_code, content=json.dumps({'error': error.detail}), headers=error.headers)

# Usage example:
# from fastapi import FastAPI
# from .middlewares.ratelimitMiddleware import RateLimiterMiddleware
#
# app = FastAPI()
# app.add_middleware(RateLimiterMiddleware, key_path='client.host')