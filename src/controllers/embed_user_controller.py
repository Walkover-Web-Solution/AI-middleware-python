from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from globals import logger
from src.db_services.embed_user_limit_service import (
    build_limit_summary,
    deactivate_embed_limit,
    get_embed_usage_record,
    reset_embed_usage,
    set_embed_usage_limit,
)


def _extract_org_id(request: Request) -> Optional[str]:
    profile = getattr(request.state, "profile", {}) or {}
    org = profile.get("org") or {}
    return org.get("id")


def _validate_user_id(user_id: Optional[Any], *, required: bool = True) -> Optional[str]:
    if user_id in (None, "", "null"):
        if required:
            raise HTTPException(status_code=400, detail="user_id is required")
        return None
    return str(user_id)


def _resolve_scope(value: Optional[str]) -> str:
    if not value:
        return "user"
    scope = value.lower()
    if scope not in {"user", "org"}:
        raise HTTPException(status_code=400, detail="scope must be either 'user' or 'org'")
    return scope


def _validate_limit(limit: Optional[Any]) -> Optional[float]:
    if limit in (None, ""):
        return None
    try:
        value = float(limit)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="limit must be a valid number") from exc
    if value < 0:
        raise HTTPException(status_code=400, detail="limit must be greater than or equal to zero")
    return value


async def upsert_embed_limit(request: Request) -> JSONResponse:
    org_id = _extract_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="Unable to resolve org_id from request context")

    body = await request.json()
    scope = _resolve_scope(body.get("scope"))
    user_id = _validate_user_id(body.get("user_id"), required=scope == "user")
    folder_id = body.get("folder_id")
    limit = _validate_limit(body.get("limit"))
    reset_frequency = body.get("reset_frequency")
    is_active = body.get("is_active", True)

    try:
        record = await set_embed_usage_limit(org_id, user_id, folder_id, limit, reset_frequency, is_active)
        summary = await build_limit_summary(record)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": summary,
            },
        )
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error(f"Failed to upsert embed usage limit: {error}")
        raise HTTPException(status_code=500, detail="Failed to update embed usage limit") from error


async def get_embed_limit(request: Request) -> JSONResponse:
    org_id = _extract_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="Unable to resolve org_id from request context")

    scope = _resolve_scope(request.query_params.get("scope"))
    user_id = _validate_user_id(request.query_params.get("user_id"), required=scope == "user")
    folder_id = request.query_params.get("folder_id")

    record = await get_embed_usage_record(org_id, user_id, folder_id)
    if not record:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "No usage limit configured for the supplied scope",
            },
        )

    summary = await build_limit_summary(record)
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": summary,
        },
    )


async def reset_embed_limit(request: Request) -> JSONResponse:
    org_id = _extract_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="Unable to resolve org_id from request context")

    body = await request.json()
    scope = _resolve_scope(body.get("scope"))
    user_id = _validate_user_id(body.get("user_id"), required=scope == "user")
    folder_id = body.get("folder_id")

    record = await reset_embed_usage(org_id, user_id, folder_id)
    if not record:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "No usage limit found to reset",
            },
        )

    summary = await build_limit_summary(record)
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": summary,
        },
    )


async def deactivate_embed_limit_controller(request: Request) -> JSONResponse:
    org_id = _extract_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="Unable to resolve org_id from request context")

    body = await request.json()
    scope = _resolve_scope(body.get("scope"))
    user_id = _validate_user_id(body.get("user_id"), required=scope == "user")
    folder_id = body.get("folder_id")

    record = await deactivate_embed_limit(org_id, user_id, folder_id)
    if not record:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "No usage limit found to deactivate",
            },
        )

    summary = await build_limit_summary(record)
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": summary,
        },
    )
