"""
Transfer Agent Configuration Handler

This module handles the extraction and processing of transfer agent configurations
from tool calls in AI model responses.
"""

import json
from typing import Dict, Any, Optional, Tuple


def extract_transfer_config(model_response: Dict[str, Any], custom_config: Dict[str, Any], service: str = 'openai') -> Tuple[bool, Dict[str, Any]]:
    """
    Extract transfer agent configuration from model response tool calls
    
    Args:
        model_response: The model response containing tool calls
        custom_config: The current agent configuration with tool mappings
        service: The service type ('openai', 'openai_response', or 'anthropic')
    
    Returns:
        Tuple of (has_transfer: bool, transfer_config: dict)
    """
    if service == 'openai_response':
        # Handle openai_response format with output array
        output_array = model_response.get('output', [])
        print(f"DEBUG openai_response: output_array = {output_array}")
        if not output_array:
            print("DEBUG openai_response: No output array found")
            return False, {}
        
        for output in output_array:
            print(f"DEBUG openai_response: Processing output = {output}")
            print(f"DEBUG openai_response: Output keys = {list(output.keys()) if isinstance(output, dict) else 'Not a dict'}")
            output_type = output.get('type') if isinstance(output, dict) else None
            print(f"DEBUG openai_response: Output type = {output_type}")
            
            # Check all possible structures in the output
            function_call_data = None
            args = None
            tool_name = ""
            
            # Check if output has direct function call info
            if isinstance(output, dict):
                # Look for various possible keys
                possible_keys = ['function_call', 'tool_call', 'function', 'name', 'arguments']
                for key in possible_keys:
                    if key in output:
                        print(f"DEBUG openai_response: Found key '{key}' in output: {output[key]}")
                
                # Condition 1: type == 'function_call'
                if output_type == 'function_call':
                    print(f"DEBUG openai_response: Found function_call type")
                    if 'function_call' in output:
                        function_call_data = output['function_call']
                    elif 'name' in output and 'arguments' in output:
                        function_call_data = {'name': output['name'], 'arguments': output['arguments']}
                    else:
                        function_call_data = output
                    
                # Condition 2: type == 'tool_call'  
                elif output_type == 'tool_call':
                    print(f"DEBUG openai_response: Found tool_call type")
                    if 'function' in output:
                        function_call_data = output['function']
                    elif 'name' in output and 'arguments' in output:
                        function_call_data = {'name': output['name'], 'arguments': output['arguments']}
                    else:
                        function_call_data = output
                        
                # Direct function call structure (no type field)
                elif 'name' in output and 'arguments' in output:
                    print(f"DEBUG openai_response: Found direct function call structure")
                    function_call_data = output
                    
                # Condition 3: 'function_call' in str(output) and type in ['reasoning', 'message', 'output_text']
                elif 'function_call' in str(output) and output_type in ['reasoning', 'message', 'output_text']:
                    print(f"DEBUG openai_response: Found function_call in {output_type} content")
                    content_str = str(output)
                    print(f"DEBUG openai_response: Content string: {content_str}")
                    
                    # Try to extract function call from the content
                    try:
                        import re
                        pattern = r'"function_call":\s*{[^}]+}'
                        match = re.search(pattern, content_str)
                        if match:
                            function_call_json = match.group(0)
                            print(f"DEBUG openai_response: Extracted function_call JSON: {function_call_json}")
                            full_json = "{" + function_call_json + "}"
                            parsed = json.loads(full_json)
                            function_call_data = parsed.get('function_call', {})
                    except Exception as e:
                        print(f"DEBUG openai_response: Failed to parse function_call from content: {e}")
                        continue
                
                if function_call_data:
                    tool_name = function_call_data.get('name', '')
                    args = function_call_data.get('arguments', {})
                    print(f"DEBUG openai_response: Extracted tool_name = {tool_name}")
                    print(f"DEBUG openai_response: Extracted args = {args}")
            
            if function_call_data and args:
                try:
                    print(f"DEBUG openai_response: function_call_data = {function_call_data}")
                    print(f"DEBUG openai_response: raw args = {args}")
                    
                    if isinstance(args, str):
                        args = json.loads(args)
                    print(f"DEBUG openai_response: parsed args = {args}")
                    
                    action_type = args.get('action_type')
                    print(f"DEBUG openai_response: action_type = {action_type}")
                    
                    if action_type == 'transfer':
                        transfer_config = {
                            "agent_id": args.get('child_agent_id', ''),
                            "tool_name": tool_name,
                            "user_query": args.get('user_query', ''),
                            "action_type": action_type,
                            "all_arguments": args,
                            "tool_call_id": output.get('id', ''),
                            "function_name": tool_name
                        }
                        
                        print(f"DEBUG openai_response: Found transfer! config = {transfer_config}")
                        return True, transfer_config
                        
                except (json.JSONDecodeError, Exception) as e:
                    print(f"DEBUG openai_response: Exception parsing function_call: {e}")
                    continue
            else:
                print(f"DEBUG openai_response: Output type is {output_type}, no function_call data found")
        
        print("DEBUG openai_response: No transfer found")
        return False, {}
    
    elif service == 'anthropic':
        # Handle anthropic format with content array
        content_array = model_response.get('content', [])
        print(f"DEBUG anthropic: content_array = {content_array}")
        if not content_array:
            print("DEBUG anthropic: No content array found")
            return False, {}
        
        for content in content_array:
            print(f"DEBUG anthropic: Processing content = {content}")
            content_type = content.get('type')
            
            if content_type == 'tool_use':
                print(f"DEBUG anthropic: Found tool_use type")
                try:
                    tool_name = content.get('name', '')
                    args = content.get('input', {})
                    print(f"DEBUG anthropic: tool_name = {tool_name}")
                    print(f"DEBUG anthropic: args = {args}")
                    
                    action_type = args.get('action_type')
                    print(f"DEBUG anthropic: action_type = {action_type}")
                    
                    if action_type == 'transfer':
                        transfer_config = {
                            "agent_id": args.get('child_agent_id', ''),
                            "tool_name": tool_name,
                            "user_query": args.get('user_query', ''),
                            "action_type": action_type,
                            "all_arguments": args,
                            "tool_call_id": content.get('id', ''),
                            "function_name": tool_name
                        }
                        
                        print(f"DEBUG anthropic: Found transfer! config = {transfer_config}")
                        return True, transfer_config
                        
                except Exception as e:
                    print(f"DEBUG anthropic: Exception parsing tool_use: {e}")
                    continue
            else:
                print(f"DEBUG anthropic: Content type is {content_type}, not tool_use")
        
        print("DEBUG anthropic: No transfer found")
        return False, {}
    
    else:
        # Handle standard openai format with choices
        if not model_response.get('choices', []):
            return False, {}
        
        tool_calls = model_response.get('choices', [])[0].get('message', {}).get("tool_calls", [])
        if not tool_calls:
            return False, {}
        
        for tool_call in tool_calls:
            function_args = tool_call.get('function', {}).get('arguments', '{}')
            try:
                args = json.loads(function_args)
                action_type = args.get('action_type')
                
                if action_type == 'transfer':
                    # Extract all arguments and create transfer config
                    tool_name = tool_call.get('function', {}).get('name', '')
                    tool_mapping = custom_config.get('tool_id_and_name_mapping', {})
                    agent_info = tool_mapping.get(tool_name, {})
                    
                    transfer_config = {
                        "agent_id": args.get('child_agent_id', ''),
                        "tool_name": tool_name,
                        "user_query": args.get('user_query', ''),
                        "action_type": action_type,
                        "all_arguments": args,
                        "tool_call_id": tool_call.get('id', ''),
                        "function_name": tool_call.get('function', {}).get('name', '')
                    }
                    
                    return True, transfer_config
                    
            except (json.JSONDecodeError, Exception) as e:
                # Continue checking other tool calls
                continue
        
        return False, {}


def should_skip_function_call(model_response: Dict[str, Any], custom_config: Dict[str, Any], service: str = 'openai') -> Tuple[bool, Dict[str, Any]]:
    """
    Check if function call should be skipped due to transfer action
    
    Args:
        model_response: The model response containing tool calls
        custom_config: The current agent configuration with tool mappings
        service: The service type ('openai', 'openai_response', or 'anthropic')
    
    Returns:
        Tuple of (should_skip: bool, transfer_config: dict)
    """
    return extract_transfer_config(model_response, custom_config, service)
