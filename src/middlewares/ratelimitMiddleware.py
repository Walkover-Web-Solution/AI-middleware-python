from ..services.cache_service import find_in_cache, store_in_cache, verify_ttl
import json
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

async def get_nested_value(request, path):
    """Extract nested value from the request object based on the key path."""
    keys = path.split('.')
    
    if keys[0] == 'body':
        request_body = await request.json()
        obj = request_body.get('body', {})
        keys = keys[1:]
    elif keys[0] == 'profile':
        obj = request.state
        keys = keys[1:]
    elif keys[0] == 'headers':
        obj = request.headers
        keys = keys[1:]
    else:
        return None

    for key in keys:
        if isinstance(obj, dict) and key in obj:
            obj = obj[key]
        elif hasattr(obj, key):
            obj = getattr(obj, key)
        else:
            return None
    return obj

async def rate_limit(request: Request, key_path: str, points: int = 40, ttl: int = 60):

    key = await get_nested_value(request, key_path)
    if not key:
        return

    redis_key = f"rate-limit:{key}"
    record = await find_in_cache(redis_key)

    if record:
        ttl = await verify_ttl(redis_key)
        data = json.loads(record)
        count = data['count']
        if count >= points:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests for {key}",
                headers={"Retry-After": str(ttl)}
            )
        data['count'] += 1
    else:
        data = {'count': 1}

    await store_in_cache(redis_key, data, ttl)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, bridge_points: int = 100, thread_points: int = 20, ttl: int = 60):
        super().__init__(app)
        self.bridge_points = bridge_points
        self.thread_points = thread_points
        self.ttl = ttl

    async def dispatch(self, request: Request, call_next):
        try:
            body = await request.json()
            bridge_id = body.get("bridge_id")
            thread_id = body.get("thread_id")

            if bridge_id:
                await rate_limit(request, bridge_id, self.bridge_points, self.ttl)
            if thread_id:
                await rate_limit(request, thread_id, self.thread_points, self.ttl)

            return await call_next(request)
        except HTTPException as error:
            return Response(status_code=error.status_code, content=json.dumps({'error': error.detail}), headers=error.headers)

# Usage example:
# from fastapi import FastAPI
# from .middlewares.ratelimitMiddleware import RateLimiterMiddleware
#
# app = FastAPI()
# app.add_middleware(RateLimiterMiddleware, key_path='client.host')