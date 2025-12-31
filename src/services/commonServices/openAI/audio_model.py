import traceback
from openai import AsyncOpenAI
import base64
import io


async def OpenAIAudioModel(configuration, apiKey, execution_time_logs, timer, audio_file):
    try:
        openai_config = AsyncOpenAI(api_key=apiKey)
        timer.start()
        
        model = configuration.get('model')
        
        # Handle base64 encoded audio - strictly require data:audio format
        if isinstance(audio_file, str):
            if not audio_file.startswith('data:audio'):
                raise ValueError("Audio file must be in 'data:audio' format (e.g., 'data:audio/mp3;base64,...')")
            
            # Extract base64 data after the comma
            base64_data = audio_file.split(',', 1)[1]
            audio_bytes = base64.b64decode(base64_data)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.mp3"  # OpenAI requires a filename
        
        # Process transcription
        chat_completion = await openai_config.audio.transcriptions.create(
            model=model,
            file=audio_file,
        )
        execution_time_logs.append({
            "step": "OpenAI audio transcription processing time", 
            "time_taken": timer.stop("OpenAI audio transcription processing time")
        })
        
        # Extract token-based usage from newer audio models
        usage_data = {}
        if hasattr(chat_completion, 'usage') and chat_completion.usage:
            usage = chat_completion.usage
            if hasattr(usage, 'input_tokens'):
                usage_data = {
                    "input_tokens": usage.input_tokens,
                    "input_token_details": dict(usage.input_token_details) if hasattr(usage, 'input_token_details') else {},
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.total_tokens
                }
        
        response = {
            'text': chat_completion.text,
            'operation': 'transcription',
            'model': model,
            'usage': usage_data
        }

        return {
            'success': True,
            'response': response
        }
    except Exception as error:
        execution_time_logs.append({
            "step": "OpenAI audio processing time", 
            "time_taken": timer.stop("OpenAI audio processing time")
        })
        print("audio model error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
