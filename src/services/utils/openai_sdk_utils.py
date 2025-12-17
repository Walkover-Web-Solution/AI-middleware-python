import json
import time
import uuid
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def format_openai_response(chat_response: Dict[str, Any], original_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    response_data = chat_response.get("response", {}).get("data", {})
    usage_data = chat_response.get("response", {}).get("usage", {}) or {}

    message_content = response_data.get("content")
    if isinstance(message_content, list):
        message_content = "\n".join(
            chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
            for chunk in message_content
        ).strip()

    finish_reason = response_data.get("finish_reason") or usage_data.get("finish_reason")
    model = original_payload.get("model") if isinstance(original_payload, dict) else None

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": message_content,
                },
                "finish_reason": finish_reason or "stop",
                "logprobs": None,
            }
        ],
        "usage": {
            "prompt_tokens": usage_data.get("input_tokens") or usage_data.get("prompt_tokens"),
            "completion_tokens": usage_data.get("output_tokens") or usage_data.get("completion_tokens"),
            "total_tokens": usage_data.get("total_tokens"),
        },
        "system_fingerprint": None,
    }


async def run_openai_chat_and_format(
    request: Request,
    db_config: Dict[str, Any],
    chat_handler: Callable[[Request, Dict[str, Any]], Awaitable[Any]],
) -> Dict[str, Any]:
    internal_response = await chat_handler(request, db_config)

    if isinstance(internal_response, JSONResponse):
        content = internal_response.body
        try:
            content_dict = json.loads(content)
        except Exception:
            content_dict = {}
        if not content_dict.get("success", True):
            raise HTTPException(status_code=500, detail=content_dict)
        chat_response = content_dict
    else:
        chat_response = internal_response

    openai_payload = getattr(request.state, "openai_payload", {})
    return format_openai_response(chat_response, openai_payload)
