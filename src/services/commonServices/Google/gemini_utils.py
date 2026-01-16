import json
from google.genai import types


def convert_to_gemini_format(config):
    """
    Convert OpenAI-style config to Gemini SDK format.
    
    Args:
        config: Dictionary with OpenAI-style structure containing:
            - messages: List of message objects
            - model: Model name
            - temperature, max_output_tokens, etc.: Generation parameters
            - tools: Optional tool definitions
    
    Returns:
        Dictionary with Gemini SDK structure containing:
            - model: Model name
            - contents: List of types.Content objects
            - config: types.GenerateContentConfig object (if parameters exist)
    """
    messages = config.get('messages', [])
    contents = []
    system_instruction = None
    
    for msg in messages:
        role = msg.get('role')
        content = msg.get('content')
        
        # Handle system/developer messages
        if role == 'developer':
            if isinstance(content, str):
                system_instruction = content
            continue
        
        # Handle assistant messages with tool calls
        if role == 'assistant' and msg.get('tool_calls'):
            parts = []
            for tool_call in msg['tool_calls']:
                fc = tool_call['function']
                parts.append(types.Part(function_call=types.FunctionCall(
                    name=fc['name'],
                    args=json.loads(fc['arguments']) if isinstance(fc['arguments'], str) else fc['arguments']
                )))
            contents.append(types.Content(role='model', parts=parts))
            continue
        
        # Handle tool response messages
        if role == 'tool':
            tool_response = msg.get('content')
            if isinstance(tool_response, str):
                try:
                    tool_response = json.loads(tool_response)
                except:
                    tool_response = {"result": tool_response}
            
            if not isinstance(tool_response, dict):
                tool_response = {"result": tool_response}

            parts = [types.Part.from_function_response(
                name=msg.get('name'),
                response=tool_response
            )]
            contents.append(types.Content(role='user', parts=parts))
            continue
        
        # Handle regular messages
        gemini_role = 'model' if role == 'assistant' else 'user'
        parts = []
        
        if isinstance(content, str) and content:
            parts.append(types.Part(text=content))
        elif isinstance(content, list):
            for item in content:
                if item.get('type') == 'text':
                    parts.append(types.Part(text=item.get('text', '')))
                elif item.get('type') == 'image_url':
                    image_url = item.get('image_url', {}).get('url', '')
                    if image_url:
                        parts.append(types.Part.from_uri(file_uri=image_url, mime_type="image/jpeg"))
        
        if parts:
            contents.append(types.Content(role=gemini_role, parts=parts))
    
    # Build Gemini config
    gemini_config = {
        'model': config.get('model'),
        'contents': contents
    }
    
    # Build generation config
    config_params = {}
    if system_instruction:
        config_params['system_instruction'] = system_instruction
    
    for key in ['temperature', 'max_output_tokens', 'top_p', 'top_k', 'stop_sequences']:
        if key in config:
            config_params[key] = config[key]
    
    # Handle tools
    if 'tools' in config and config['tools']:
        tool_declarations = []
        for tool in config['tools']:
            if 'function' in tool:
                tool_declarations.append(tool['function'])
        if tool_declarations:
            config_params['tools'] = [types.Tool(function_declarations=tool_declarations)]
    
    if config_params:
        gemini_config['config'] = types.GenerateContentConfig(**config_params)
    
    return gemini_config
