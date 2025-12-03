import traceback
from io import BytesIO
from typing import Dict, Any, List
from google import genai
from google.genai import types

from src.services.utils.gcp_upload_service import uploadDoc
from globals import logger

SUPPORTED_VIDEO_MODELS = {
    "veo-2.0-generate",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro"
}

MODEL_FALLBACKS = {
    "veo-3.1-generate-preview": "veo-2.0-generate",
    "veo-3.1-fast-generate-preview": "veo-2.0-generate"
}


def _prepare_contents(prompt_or_contents):
    if isinstance(prompt_or_contents, str):
        return prompt_or_contents
    if isinstance(prompt_or_contents, list):
        return prompt_or_contents
    if isinstance(prompt_or_contents, dict):
        return [types.Content(parts=[types.Part(text=prompt_or_contents.get('text', ''))])]
    return ""


def _serialize_file_part(part) -> Dict[str, Any]:
    file_data = getattr(part, "file_data", None)
    if not file_data:
        return {}
    return {
        "file_uri": getattr(file_data, "file_uri", None),
        "mime_type": getattr(file_data, "mime_type", None),
        "display_name": getattr(file_data, "display_name", None)
    }


async def gemini_video_generation_model(configuration, apikey, execution_time_logs, timer, video_settings=None):
    """Generate videos using Gemini models, mirroring image generation flow."""
    try:
        client = genai.Client(api_key=apikey)
        prompt = configuration.pop('prompt', '')
        requested_model = configuration.pop('model')

        resolved_model = requested_model
        if requested_model in MODEL_FALLBACKS:
            resolved_model = MODEL_FALLBACKS[requested_model]
            logger.warning(
                "Gemini video model %s not supported; falling back to %s",
                requested_model,
                resolved_model
            )
        elif requested_model not in SUPPORTED_VIDEO_MODELS:
            supported = ", ".join(sorted(SUPPORTED_VIDEO_MODELS | set(MODEL_FALLBACKS.values())))
            raise ValueError(
                f"Model '{requested_model}' is not supported for video generation. Supported models: {supported}"
            )

        model = resolved_model
        video_config = configuration.pop('video_settings', {}) or {}
        config = configuration.copy()
        combined_settings = {}
        if isinstance(video_config, dict):
            combined_settings.update(video_config)
        if isinstance(video_settings, dict):
            combined_settings.update(video_settings)

        contents = _prepare_contents(prompt)

        timer.start()
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config) if config else None
        )
        execution_time_logs.append({
            "step": "Gemini video generation",
            "time_taken": timer.stop("Gemini video generation")
        })

        text_content: List[str] = []
        video_files: List[Dict[str, Any]] = []

        for part in response.candidates[0].content.parts:
            if getattr(part, 'text', None):
                text_content.append(part.text)
                continue

            inline_data = getattr(part, 'inline_data', None)
            if inline_data and getattr(inline_data, 'data', None):
                buffer = BytesIO(inline_data.data)
                video_url = await uploadDoc(
                    file=buffer,
                    folder='generated-videos',
                    real_time=True,
                    content_type=getattr(inline_data, 'mime_type', 'video/mp4')
                )
                video_files.append({
                    "file_uri": video_url,
                    "mime_type": getattr(inline_data, 'mime_type', 'video/mp4'),
                    "storage": "gcp"
                })
                continue

            serialized = _serialize_file_part(part)
            if serialized:
                video_files.append(serialized)

        return {
            "success": True,
            "response": {
                "data": [{
                    "text_content": text_content,
                    "video_files": video_files,
                    "metadata": combined_settings
                }]
            }
        }

    except Exception as error:
        execution_time_logs.append({
            "step": "Gemini video generation error",
            "time_taken": timer.stop("Gemini video generation error")
        })
        print("gemini_video_generation_model error=>", error)
        traceback.print_exc()
        return {
            "success": False,
            "error": str(error)
        }
