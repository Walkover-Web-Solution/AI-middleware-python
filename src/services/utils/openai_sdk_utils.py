import json
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def _build_output_blocks(message_content: str) -> List[Dict[str, Any]]:
    reasoning_block = {
        "id": f"rs_{uuid.uuid4().hex}",
        "type": "reasoning",
        "summary": [],
    }

    message_block = {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "status": "completed",
        "role": "assistant",
        "content": [
            {
                "type": "output_text",
                "text": message_content,
            }
        ],
    }

    return [reasoning_block, message_block]


def format_openai_response(chat_response: Dict[str, Any], original_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    response_data = chat_response.get("response", {}).get("data", {})
    usage_data = chat_response.get("response", {}).get("usage", {}) or {}

    message_content = response_data.get("content")
    if isinstance(message_content, list):
        message_content = "\n".join(
            chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
            for chunk in message_content
        ).strip()
    elif not isinstance(message_content, str):
        message_content = str(message_content or "")

    message_content = message_content.strip()
    finish_reason = response_data.get("finish_reason") or usage_data.get("finish_reason")
    model = original_payload.get("model") if isinstance(original_payload, dict) else None

    response_id = f"resp_{uuid.uuid4().hex}"
    created_at = int(time.time())

    return {
        "id": response_id,
        "object": "response",
        "created_at": created_at,
        "status": "completed",
        "background": False,
        "billing": {"payer": "developer"},
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "max_tool_calls": None,
        "model": model,
        "output": _build_output_blocks(message_content),
        "parallel_tool_calls": True,
        "previous_response_id": None,
        "prompt_cache_key": None,
        "prompt_cache_retention": None,
        "reasoning": {"effort": "medium", "summary": None},
        "safety_identifier": None,
        "service_tier": "default",
        "store": True,
        "temperature": original_payload.get("temperature") if isinstance(original_payload, dict) else None,
        "text": {"format": {"type": "text"}, "verbosity": "medium"},
        "tool_choice": original_payload.get("tool_choice") if isinstance(original_payload, dict) else "auto",
        "tools": original_payload.get("tools") if isinstance(original_payload, dict) else [],
        "top_logprobs": 0,
        "top_p": original_payload.get("top_p") if isinstance(original_payload, dict) else 1,
        "truncation": "disabled",
        "usage": {
            "input_tokens": usage_data.get("input_tokens"),
            "input_tokens_details": {
                "cached_tokens": usage_data.get("cached_input_tokens", 0),
            },
            "output_tokens": usage_data.get("output_tokens"),
            "output_tokens_details": {
                "reasoning_tokens": usage_data.get("reasoning_tokens"),
            },
            "total_tokens": usage_data.get("total_tokens"),
        },
        "user": original_payload.get("user") if isinstance(original_payload, dict) else None,
        "metadata": original_payload.get("metadata") if isinstance(original_payload, dict) else {},
        "output_text": message_content,
        "finish_reason": finish_reason or "stop",
    }


def _format_error_detail(
    message: str,
    error_type: str = "invalid_request_error",
    code: Optional[str] = None,
    param: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": error_type,
            "param": param,
            "code": code,
        }
    }


def _extract_error_message(error_payload: Dict[str, Any]) -> str:
    error_value = error_payload.get("error")

    if isinstance(error_value, str):
        return error_value

    if isinstance(error_value, dict):
        return error_value.get("message") or error_value.get("detail") or json.dumps(error_value)

    if isinstance(error_payload.get("detail"), str):
        return error_payload["detail"]

    return json.dumps(error_payload)


def _handle_failed_response(
    response_payload: Dict[str, Any],
    status_code: int = 400,
) -> None:
    message = _extract_error_message(response_payload)
    error_type = response_payload.get("error_type") or "invalid_request_error"
    code = response_payload.get("error_code")
    param = response_payload.get("error_param")

    raise HTTPException(
        status_code=status_code,
        detail=_format_error_detail(message, error_type=error_type, code=code, param=param),
    )


async def run_openai_chat_and_format(
    request: Request,
    db_config: Dict[str, Any],
    chat_handler: Callable[[Request, Dict[str, Any]], Awaitable[Any]],
) -> Dict[str, Any]:
    openai_payload = getattr(request.state, "openai_payload", {})
    internal_response = await chat_handler(request, db_config)

    if isinstance(internal_response, JSONResponse):
        content = internal_response.body
        try:
            content_dict = json.loads(content)
        except Exception:
            content_dict = {}
        if not content_dict.get("success", True):
            status_code = content_dict.get("status_code") or 400
            _handle_failed_response(content_dict, status_code=status_code)
        chat_response = content_dict
    else:
        chat_response = internal_response

    if isinstance(chat_response, dict) and not chat_response.get("success", True):
        status_code = chat_response.get("status_code") or 400
        _handle_failed_response(chat_response, status_code=status_code)

    return format_openai_response(chat_response, openai_payload)
