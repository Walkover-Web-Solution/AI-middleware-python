import json
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Request
from .middleware import jwt_middleware
from .ratelimitMiddleware import rate_limit


def _extract_pauthkey_from_authorization(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header with Bearer pauthkey is required.",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token cannot be empty.")
    return token


def _normalize_message_content(content: Any) -> Optional[str]:
    if isinstance(content, str):
        content = content.strip()
        return content or None

    if isinstance(content, list):
        text_parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                item_type = (item.get("type") or "").lower()
                if item_type in {"text", "input_text", "output_text"}:
                    text_value = (item.get("text") or "").strip()
                    if text_value:
                        text_parts.append(text_value)
        merged = "\n".join(text_parts).strip()
        return merged or None

    return None


def _extract_latest_user_message(messages: List[Dict[str, Any]]) -> Optional[str]:
    for message in reversed(messages or []):
        if message.get("role") != "user":
            continue
        normalized = _normalize_message_content(message.get("content"))
        if normalized:
            return normalized
    return None


def _extract_text_from_input(input_value: Any) -> Optional[str]:
    if isinstance(input_value, str):
        text = input_value.strip()
        return text or None

    if isinstance(input_value, dict):
        return _normalize_message_content(input_value.get("content"))

    if isinstance(input_value, list):
        segments: List[str] = []
        for chunk in input_value:
            if isinstance(chunk, dict):
                content = chunk.get("content")
                extracted = _normalize_message_content(content)
                if extracted:
                    segments.append(extracted)
                elif isinstance(chunk.get("text"), str):
                    text_value = chunk["text"].strip()
                    if text_value:
                        segments.append(text_value)
        merged = "\n".join(segments).strip()
        return merged or None

    return None


def _extract_agent_identifier(payload: Dict[str, Any]) -> str:
    agent_id = payload.get("agent_id") or payload.get("bridge_id")

    if isinstance(agent_id, str):
        agent_id = agent_id.strip()
    if not agent_id:
        raise HTTPException(
            status_code=400,
            detail="`agent_id` must be included in the request body.",
        )
    return str(agent_id)


def _build_internal_body(payload: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = _extract_agent_identifier(payload)
    llm_model = payload.get("model")

    user_message = _extract_latest_user_message(payload.get("messages", []))
    if not user_message:
        fallback = payload.get("input") or payload.get("prompt")
        user_message = _extract_text_from_input(fallback)
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found in payload.")

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    configuration = payload.get("configuration") or {}
    if not isinstance(configuration, dict):
        configuration = {}

    if isinstance(llm_model, str) and llm_model.strip():
        configuration.setdefault("model", llm_model.strip())

    response_format = payload.get("response_format")
    if response_format:
        if isinstance(response_format, dict):
            configuration.setdefault("response_format", response_format)
        elif isinstance(response_format, str):
            configuration.setdefault(
                "response_format",
                {
                    "type": response_format,
                    "cred": {},
                },
            )

    internal_body: Dict[str, Any] = {
        "agent_id": agent_id,
        "bridge_id": agent_id,
        "user": user_message,
        "messages": payload.get("messages", []),
        "thread_id": payload.get("conversation_id")
        or payload.get("thread_id")
        or metadata.get("thread_id"),
        "sub_thread_id": payload.get("sub_thread_id") or metadata.get("sub_thread_id"),
        "variables": payload.get("variables") or metadata.get("variables") or {},
        "configuration": configuration,
        "attachments": payload.get("attachments", []),
    }

    return internal_body


def _override_request_body(request: Request, body: Dict[str, Any]) -> None:
    body_bytes = json.dumps(body).encode("utf-8")
    request._body = body_bytes  # type: ignore[attr-defined]
    request._json = body  # type: ignore[attr-defined]
    request._stream_consumed = True  # type: ignore[attr-defined]
    if "_form" in request.__dict__:
        request.__dict__.pop("_form")


def _set_pauthkey_header(request: Request, token: str) -> None:
    raw_headers = list(request.scope.get("headers", []))
    filtered_headers = [
        (name, value)
        for name, value in raw_headers
        if name.lower() != b"authorization"
    ]
    filtered_headers.append((b"pauthkey", token.encode("utf-8")))
    request.scope["headers"] = filtered_headers
    if "_headers" in request.__dict__:
        del request.__dict__["_headers"]


async def openai_sdk_middleware(request: Request):
    payload = await request.json()
    internal_body = _build_internal_body(payload)
    token = _extract_pauthkey_from_authorization(request)

    _override_request_body(request, internal_body)
    _set_pauthkey_header(request, token)
    request.state.openai_payload = payload

    await jwt_middleware(request)
    await rate_limit(request, key_path="body.bridge_id", points=100)
    await rate_limit(request, key_path="body.thread_id", points=20)