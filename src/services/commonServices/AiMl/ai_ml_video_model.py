import asyncio
import time
from io import BytesIO

from src.services.utils.apiservice import fetch
from src.services.utils.gcp_upload_service import uploadDoc
from globals import logger


AI_ML_BASE_URL = "https://api.ai.ml"


def _build_directive_string(settings):
    if not isinstance(settings, dict):
        return ""

    directives = []
    mapping = {
        'resolution': '--resolution {}',
        'duration_seconds': '--duration {}',
        'camera_fixed': '--camerafixed {}',
        'camerafixed': '--camerafixed {}',
        'frame_rate': '--framerate {}'
    }

    for key, template in mapping.items():
        if key in settings and settings[key] not in [None, ""]:
            value = str(settings[key]).lower() if key in {'camera_fixed', 'camerafixed'} else settings[key]
            directives.append(template.format(value))

    return " ".join(directives)


def _prepare_content(prompt, directives, base_content=None, image_urls=None):
    content = []
    if isinstance(base_content, list):
        for item in base_content:
            if isinstance(item, dict) and item.get('type') in {'text', 'image_url'}:
                content.append(item)

    final_prompt = prompt or ""
    if directives:
        final_prompt = f"{final_prompt.strip()} {directives}".strip()

    if final_prompt:
        content.insert(0, {"type": "text", "text": final_prompt})

    if image_urls:
        for url in image_urls:
            if url:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })

    return content


async def _poll_task(api_key, task_id, poll_interval=3, timeout=600):
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            task_response, _ = await fetch(
                f"{AI_ML_BASE_URL}/v1/generation/tasks/video/{task_id}",
                headers=headers
            )
        except Exception as error:
            logger.warning("AI.ML poll error for %s: %s", task_id, str(error))
            await asyncio.sleep(poll_interval)
            continue

        data = task_response.get('data', {})
        status = data.get('status')

        if status == 'succeeded':
            return data
        if status == 'failed':
            raise ValueError(f"AI.ML video generation failed: {task_response}")
        if status == 'canceled':
            raise ValueError("AI.ML video generation was canceled")

        await asyncio.sleep(poll_interval)

    raise TimeoutError("AI.ML video generation timed out")


async def _resolve_media_url(api_key, media_path):
    headers = {"Authorization": f"Bearer {api_key}"}
    response, _ = await fetch(f"{AI_ML_BASE_URL}{media_path}", headers=headers)
    presigned_url = response.get('url')
    if not presigned_url:
        raise ValueError("AI.ML media resolution did not return a URL")
    return presigned_url


async def _download_video(presigned_url):
    video_stream, response_headers = await fetch(presigned_url, image=True)
    video_stream.seek(0)
    content_type = response_headers.get('Content-Type', 'video/mp4')
    return video_stream, content_type


def _extract_video_path(payload, depth=0, visited=None):
    if depth > 10:
        return None
    if not isinstance(payload, dict):
        return None
    visited = visited or set()
    payload_id = id(payload)
    if payload_id in visited:
        return None
    visited.add(payload_id)

    candidates = [
        payload.get('videoUrl')
    ]

    nested_candidates = [
        payload.get('result', {}),
        payload.get('output', {}),
        payload.get('outputs', {}),
        payload.get('data', {}),
        payload.get('media', {})
    ]

    for candidate in candidates:
        if candidate:
            return candidate

    for nested in nested_candidates:
        if isinstance(nested, dict):
            nested_path = _extract_video_path(nested, depth + 1, visited)
            if nested_path:
                return nested_path
        elif isinstance(nested, list):
            for entry in nested:
                nested_path = _extract_video_path(entry, depth + 1, visited)
                if nested_path:
                    return nested_path
    return None


async def _fetch_video_media(api_key, task_id):
    headers = {"Authorization": f"Bearer {api_key}"}
    fallback_paths = [
        f"{AI_ML_BASE_URL}/v1/generation/tasks/video/{task_id}?include=media",
        f"{AI_ML_BASE_URL}/v1/generation/tasks/video/{task_id}/result",
        f"{AI_ML_BASE_URL}/v1/generation/tasks/video/{task_id}/media",
        f"{AI_ML_BASE_URL}/v1/generation/tasks/video/{task_id}/videos"
    ]

    for endpoint in fallback_paths:
        try:
            response, _ = await fetch(endpoint, headers=headers)
            media_path = _extract_video_path(response)
            if media_path:
                return media_path
        except Exception as error:
            logger.warning("AI.ML media lookup failed for %s: %s", endpoint, str(error))
            continue
    return None


async def ai_ml_video_generation_model(configuration, apikey, execution_time_logs, timer, video_settings=None, prompt=None, image_urls=None):
    try:
        model = configuration.pop('model')
        video_config = configuration.pop('video_settings', {}) or {}
        combined_settings = {}
        if isinstance(video_config, dict):
            combined_settings.update(video_config)
        if isinstance(video_settings, dict):
            combined_settings.update(video_settings)

        directives = _build_directive_string(combined_settings)
        content = _prepare_content(
            prompt or configuration.pop('prompt', ''),
            directives,
            configuration.pop('content', []),
            image_urls
        )

        if not content:
            raise ValueError("AI.ML video generation requires at least one text prompt")

        headers = {
            "Authorization": f"Bearer {apikey}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "content": content
        }

        timer.start()
        creation_response, _ = await fetch(
            f"{AI_ML_BASE_URL}/v1/generation/tasks/video",
            method="POST",
            headers=headers,
            json_body=payload
        )
        execution_time_logs.append({
            "step": "AI.ML video task creation",
            "time_taken": timer.stop("AI.ML video task creation")
        })

        task_id = creation_response.get('data', {}).get('uuid')
        if not task_id:
            raise ValueError("AI.ML did not return a task UUID")

        timer.start()
        task_data = await _poll_task(apikey, task_id)
        execution_time_logs.append({
            "step": "AI.ML video task polling",
            "time_taken": timer.stop("AI.ML video task polling")
        })

        media_path = _extract_video_path(task_data)
        if not media_path:
            media_path = await _fetch_video_media(apikey, task_id)

        if not media_path:
            logger.error("AI.ML video task missing media path: %s", task_data)
            raise ValueError("AI.ML task succeeded but videoUrl is missing")

        timer.start()
        presigned_url = await _resolve_media_url(apikey, media_path)
        video_stream, content_type = await _download_video(presigned_url)
        execution_time_logs.append({
            "step": "AI.ML video download",
            "time_taken": timer.stop("AI.ML video download")
        })

        gcp_url = await uploadDoc(
            file=video_stream,
            folder='generated-videos',
            real_time=True,
            content_type=content_type
        )

        return {
            "success": True,
            "response": {
                "data": [{
                    "text_content": content[0].get('text') if content else None,
                    "video_files": [{
                        "file_uri": gcp_url,
                        "mime_type": content_type,
                        "storage": "gcp",
                        "provider_task_id": task_id
                    }],
                    "metadata": combined_settings,
                    "provider_url": presigned_url
                }]
            }
        }

    except Exception as error:
        logger.error(f"AI.ML video generation error: {str(error)}")
        return {
            "success": False,
            "error": str(error)
        }
