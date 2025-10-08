from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pymongo import ReturnDocument

from globals import logger
from models.mongo_connection import db

EMBED_LIMIT_COLLECTION = db["embed_user_limits"]

VALID_RESET_FREQUENCIES = {"none", "daily", "weekly", "monthly"}


def _utcnow() -> datetime:
    """Return a naive UTC datetime suitable for Mongo storage."""
    return datetime.utcnow().replace(tzinfo=None)


def _normalize_frequency(value: Optional[str]) -> str:
    if not value:
        return "monthly"
    value = value.lower()
    if value not in VALID_RESET_FREQUENCIES:
        logger.warning(f"Unsupported reset frequency '{value}', defaulting to monthly.")
        return "monthly"
    return value


def _normalize_folder_id(folder_id: Optional[str]) -> Optional[str]:
    folder_id = str(folder_id) if folder_id not in (None, "", "null") else None
    return folder_id


def _add_month(value: datetime) -> datetime:
    month = value.month - 1 + 1
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _calculate_period_end(start: datetime, frequency: str) -> Optional[datetime]:
    if frequency == "none":
        return None
    if frequency == "daily":
        return start + timedelta(days=1)
    if frequency == "weekly":
        return start + timedelta(weeks=1)
    if frequency == "monthly":
        return _add_month(start)
    # Should never happen because we normalize frequency, but keep a fallback.
    logger.warning(f"Unknown reset frequency '{frequency}', disabling reset.")
    return None


def _build_filter(org_id: Any, user_id: Any, folder_id: Optional[str]) -> Dict[str, Any]:
    return {
        "org_id": str(org_id) if org_id is not None else None,
        "user_id": str(user_id) if user_id is not None else None,
        "folder_id": _normalize_folder_id(folder_id),
    }


async def _ensure_current_period(record: Dict[str, Any]) -> Dict[str, Any]:
    """Reset consumed usage if the configured period has elapsed."""
    frequency = _normalize_frequency(record.get("reset_frequency"))
    if frequency == "none":
        return record

    now = _utcnow()
    period_end = record.get("period_end")
    period_start = record.get("period_start")

    if period_start is None or period_end is None or now >= period_end:
        next_end = _calculate_period_end(now, frequency)
        updated = await EMBED_LIMIT_COLLECTION.find_one_and_update(
            {"_id": record["_id"]},
            {
                "$set": {
                    "consumed": 0.0,
                    "period_start": now,
                    "period_end": next_end,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return updated or record
    return record


async def get_embed_usage_record(
    org_id: Any,
    user_id: Optional[Any],
    folder_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetch the embed usage document for the supplied identity and reset the window if needed.
    """
    filter_doc = _build_filter(org_id, user_id, folder_id)
    record = await EMBED_LIMIT_COLLECTION.find_one(filter_doc)
    if not record:
        return None
    return await _ensure_current_period(record)


async def set_embed_usage_limit(
    org_id: Any,
    user_id: Optional[Any],
    folder_id: Optional[str],
    limit: Optional[float],
    reset_frequency: Optional[str] = None,
    is_active: bool = True,
) -> Dict[str, Any]:
    """
    Create or update a cost limit for an embed user.
    """
    folder_id = _normalize_folder_id(folder_id)
    filter_doc = _build_filter(org_id, user_id, folder_id)
    now = _utcnow()
    frequency = _normalize_frequency(reset_frequency)
    limit_value = float(limit) if limit is not None else None

    update: Dict[str, Any] = {
        "$set": {
            "limit": limit_value,
            "reset_frequency": frequency,
            "is_active": bool(is_active),
            "updated_at": now,
            "scope": "org" if user_id is None else "user",
        },
        "$setOnInsert": {
            "consumed": 0.0,
            "request_count": 0,
            "created_at": now,
            "period_start": now,
            "period_end": _calculate_period_end(now, frequency),
        },
    }

    record = await EMBED_LIMIT_COLLECTION.find_one_and_update(
        filter_doc,
        update,
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return record


async def reset_embed_usage(
    org_id: Any,
    user_id: Optional[Any],
    folder_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Reset the consumed usage counter to zero and refresh the billing window.
    """
    record = await get_embed_usage_record(org_id, user_id, folder_id)
    if not record:
        return None
    frequency = _normalize_frequency(record.get("reset_frequency"))
    now = _utcnow()
    return await EMBED_LIMIT_COLLECTION.find_one_and_update(
        {"_id": record["_id"]},
        {
            "$set": {
                "consumed": 0.0,
                "updated_at": now,
                "period_start": now,
                "period_end": _calculate_period_end(now, frequency),
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def record_embed_usage_cost(
    org_id: Any,
    user_id: Optional[Any],
    folder_id: Optional[str],
    amount: float,
) -> Optional[Dict[str, Any]]:
    """
    Increment the consumed cost for an embed user. Returns the updated record if one exists.
    """
    try:
        cost = float(amount)
    except (TypeError, ValueError):
        logger.error(f"Invalid embed usage amount: {amount}")
        return None

    folder_id = _normalize_folder_id(folder_id)
    filter_doc = _build_filter(org_id, user_id, folder_id)
    now = _utcnow()

    update = {
        "$inc": {
            "consumed": cost,
            "request_count": 1,
        },
        "$set": {
            "last_cost": cost,
            "last_usage_at": now,
            "updated_at": now,
        },
    }

    record = await EMBED_LIMIT_COLLECTION.find_one_and_update(
        filter_doc,
        update,
        return_document=ReturnDocument.AFTER,
    )
    return record


async def deactivate_embed_limit(
    org_id: Any,
    user_id: Optional[Any],
    folder_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Mark an embed cost limit as inactive so it no longer gates requests.
    """
    folder_id = _normalize_folder_id(folder_id)
    filter_doc = _build_filter(org_id, user_id, folder_id)
    now = _utcnow()

    return await EMBED_LIMIT_COLLECTION.find_one_and_update(
        filter_doc,
        {
            "$set": {
                "is_active": False,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def build_limit_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct a serializable summary payload for API responses.
    """
    limit = record.get("limit")
    consumed = record.get("consumed", 0.0) or 0.0
    remaining = None
    if limit is not None:
        remaining = max(0.0, float(limit) - float(consumed))

    return {
        "org_id": record.get("org_id"),
        "user_id": record.get("user_id"),
        "folder_id": record.get("folder_id"),
        "limit": limit,
        "consumed": consumed,
        "remaining": remaining,
        "reset_frequency": record.get("reset_frequency"),
        "period_start": record.get("period_start"),
        "period_end": record.get("period_end"),
        "is_active": record.get("is_active", True),
        "last_usage_at": record.get("last_usage_at"),
        "request_count": record.get("request_count", 0),
        "scope": record.get("scope") or ("org" if record.get("user_id") in (None, "None") else "user"),
    }


async def get_embed_usage_limits(
    org_id: Any,
    user_id: Optional[Any],
    folder_id: Optional[str] = None,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fetch both user-level and org-level usage records for embed limits.
    """
    user_record = None
    if user_id is not None:
        user_record = await get_embed_usage_record(org_id, user_id, folder_id)
    org_record = await get_embed_usage_record(org_id, None, folder_id)
    return {"user": user_record, "org": org_record}


__all__ = [
    "build_limit_summary",
    "deactivate_embed_limit",
    "get_embed_usage_limits",
    "get_embed_usage_record",
    "record_embed_usage_cost",
    "reset_embed_usage",
    "set_embed_usage_limit",
]
