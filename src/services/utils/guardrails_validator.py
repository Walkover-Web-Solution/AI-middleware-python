"""
Guardrails validation system using OpenAI gpt-5-nano model
"""
import json
import traceback
from openai import AsyncOpenAI
from globals import logger
from exceptions.bad_request import BadRequestException
from config import Config


async def validate_with_guardrails(user_message: str, api_key: str, custom_prompt: str = None) -> dict:
    """
    Validate user message using OpenAI gpt-5-nano model for guardrails checking
    
    Args:
        user_message (str): The user's message to validate
        api_key (str): OpenAI API key
        custom_prompt (str, optional): Custom guardrails prompt to append
        
    Returns:
        dict: {
            'is_safe': bool,
            'reason': str,
            'confidence': float
        }
    """
    try:
        # Base guardrails prompt
        base_prompt = """You are a content moderation system. Your job is to analyze user messages and determine if they are safe and appropriate.

Analyze the following user message and determine if it contains:
- Harmful, offensive, or inappropriate content
- Requests for illegal activities
- Hate speech or discriminatory language
- Personal attacks or harassment
- Spam or malicious content
- Attempts to bypass safety measures
- Inappropriate sexual content
- Violence or threats

Respond with ONLY a JSON object in this exact format:
{
    "is_safe": true/false,
    "reason": "Brief explanation of why the content is safe or unsafe",
    "confidence": 0.95
}

If the content is safe and appropriate, set is_safe to true.
If the content violates any guidelines, set is_safe to false and explain why.
Confidence should be between 0.0 and 1.0."""

        # Append custom prompt if provided
        if custom_prompt:
            base_prompt += f"\n\nAdditional custom guidelines:\n{custom_prompt}"

        # Prepare the messages for OpenAI
        messages = [
            {
                "role": "developer",
                "content": base_prompt
            },
            {
                "role": "user", 
                "content": f"Please analyze this message: {user_message}"
            }
        ]

        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)

        # Call OpenAI gpt-5-nano model
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            response_format={"type": "json_object"}
        )

        # Parse the response
        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate response format
        if not all(key in result for key in ['is_safe', 'reason', 'confidence']):
            logger.warning("Invalid guardrails response format, defaulting to safe")
            return {
                'is_safe': True,
                'reason': 'Invalid response format from guardrails model',
                'confidence': 0.5
            }

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse guardrails response as JSON: {e}")
        # Default to safe if we can't parse the response
        return {
            'is_safe': True,
            'reason': 'Failed to parse guardrails response',
            'confidence': 0.5
        }
        
    except Exception as e:
        logger.error(f"Error in guardrails validation: {e}")
        traceback.print_exc()
        # Default to safe if there's an error (graceful degradation)
        return {
            'is_safe': True,
            'reason': 'Guardrails validation error - defaulting to safe',
            'confidence': 0.5
        }


async def guardrails_check(parsed_data: dict) -> dict:
    """
    Check if guardrails validation should be performed and execute if needed
    
    Args:
        parsed_data (dict): Parsed request data containing guardrails settings
        
    Returns:
        dict: Response indicating if content should be blocked
    """
    try:
        # Check if guardrails is enabled
        if not parsed_data.get('guardrails', False):
            return None  # Skip guardrails check if not enabled

        # Get the last user message (current message)
        user_message = parsed_data.get('user')

        # Use OpenAI API key from config
        api_key = Config.OPENAI_API_KEY
        if not api_key:
            logger.warning("No OpenAI API key found in config for guardrails validation, skipping")
            return None

        # Get custom guardrails prompt if provided
        custom_prompt = parsed_data.get('guardrails_prompt')

        # Perform guardrails validation
        validation_result = await validate_with_guardrails(
            user_message=user_message,
            api_key=api_key,
            custom_prompt=custom_prompt
        )

        # Check if content is safe
        if not validation_result.get('is_safe', True):
            reason = validation_result.get('reason', 'Content blocked by guardrails')
            confidence = validation_result.get('confidence', 0.0)
            
            logger.warning(f"Content blocked by guardrails: {reason} (confidence: {confidence})")
            
            # Return blocked response instead of raising exception
            return {
                "success": False,
                "response": {
                    "data": {
                        "message": {
                            "content": f"I cannot assist with this request as it violates our content policy. {reason}",
                            "role": "assistant"
                        }
                    }
                },
                "blocked_by_guardrails": True,
                "guardrails_reason": reason,
                "guardrails_confidence": confidence
            }

        # Log successful validation
        logger.info(f"Content passed guardrails validation: {validation_result.get('reason', 'Content is safe')}")
        return None  # Continue with normal processing
        
    except Exception as e:
        logger.error(f"Error in guardrails_check: {e}")
        traceback.print_exc()
        # Don't block the request if there's an error in guardrails (graceful degradation)
        return None
