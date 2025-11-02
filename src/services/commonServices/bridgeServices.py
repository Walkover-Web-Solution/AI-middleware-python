from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.services.prebuilt_prompt_service import get_specific_prebuilt_prompt_service
from src.db_services.ConfigurationServices import get_bridges, get_bridges_with_tools
from src.configs.constant import bridge_ids
from src.services.utils.ai_call_util import call_ai_middleware
from src.db_services.testcase_services import create_testcase
from globals import *
import re

async def optimize_prompt_controller(request : Request, bridge_id: str):
    try:
        body = await request.json()
        version_id = body.get('version_id')
        variables = {
          "query": body.get('query') or ""
        }
        thread_id = body.get('thread_id') or None
        org_id = request.state.profile.get("org",{}).get("id","")
        result = await get_bridges(bridge_id, org_id, version_id)
        bridge = result.get('bridges')
        prompt = bridge.get('configuration',{}).get('prompt',"")
        result = ""
        configuration = None
        updated_prompt = await get_specific_prebuilt_prompt_service(org_id, 'optimze_prompt')
        if updated_prompt and updated_prompt.get('optimze_prompt'):
            configuration = {"prompt": updated_prompt['optimze_prompt']}
        result = await call_ai_middleware(
            prompt, 
            variables=variables, 
            configuration=configuration, 
            thread_id=thread_id, 
            bridge_id = bridge_ids['optimze_prompt'], 
            response_type='text'
        )
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Prompt optimized successfully",
            "result" : result
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in optimizing prompt: "+ str(e)})
    
async def generate_summary(request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org",{}).get("id","")
        version_id = body.get('version_id')
        get_version_data = (await get_bridges_with_tools(None, org_id, version_id)).get("bridges")
        if not get_version_data:
            return {
                "success": False,
                "error": "Version data not found"
            }
        tools = {tool['endpoint_name']: tool['description'] for tool in get_version_data.get('apiCalls', {}).values()}
        system_prompt = get_version_data.get('configuration',{}).get('prompt')
        if tools:
            system_prompt += f'Available tool calls :-  {tools}'
        variables = {'prompt' : system_prompt}
        user = "generate summary from the user message provided in system prompt"
        configuration = None
        updated_prompt = await get_specific_prebuilt_prompt_service(org_id, 'generate_summary')
        if updated_prompt and updated_prompt.get('generate_summary'):
            configuration = {"prompt": updated_prompt['generate_summary']}
        summary = await call_ai_middleware(user, bridge_id = bridge_ids['generate_summary'], configuration=configuration, response_type='text', variables = variables)
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Summary generated successfully",
            "result" : summary
        })
            
    except Exception as err:
        logger.error("Error calling function generate_summary =>", err)
async def function_agrs_using_ai(request):
    try:
        body = await request.json()
        data = body.get('example_json')
        user = f"geneate the json using the example json data : {data}"
        json = await call_ai_middleware(user, bridge_id = bridge_ids['function_agrs_using_ai'])
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "json generated successfully",
            "result" : json
        })
            
    except Exception as err:
        logger.error("Error calling function function_agrs_using_ai =>", err)

async def generate_additional_test_cases(request: Request, bridge_id: str):
    try:
        # Check if request has body and parse JSON
        try:
            body = await request.json()
        except Exception as json_error:
            raise HTTPException(status_code=400, detail={
                "success": False, 
                "error": f"Invalid or missing JSON in request body: {str(json_error)}"
            })
        
        if not body:
            raise HTTPException(status_code=400, detail={
                "success": False, 
                "error": "Request body is required"
            })
            
        version_id = body.get('version_id')
        org_id = request.state.profile.get("org",{}).get("id","")
        
        # Get bridge data with tools using version_id
        result = await get_bridges_with_tools(bridge_id, org_id, version_id)
        bridge_data = result.get('bridges')
        
        if not bridge_data:
            raise HTTPException(status_code=404, detail={"success": False, "error": "Bridge data not found"})
        
        # Extract bridge information
        system_prompt = bridge_data.get('configuration',{}).get('prompt', "")
        tools = {tool['endpoint_name']: tool['description'] for tool in bridge_data.get('apiCalls', {}).values()}
        
        # Prepare variables for AI call
        variables = {
            "system_prompt": system_prompt,
            "available_tools": tools if tools else "No tools available"
        }
        
        # Get prebuilt prompt for test case generation if available
        configuration = None
        updated_prompt = await get_specific_prebuilt_prompt_service(org_id, 'generate_test_cases')
        if updated_prompt and updated_prompt.get('generate_test_cases'):
            configuration = {"prompt": updated_prompt['generate_test_cases']}
        
        # Generate test cases using AI
        user_message = "Generate 10 comprehensive test cases for this AI assistant based on its system prompt and available tools. Each test case should include a UserInput and ExpectedOutput."
        Testcases = await call_ai_middleware(
            user_message, 
            variables=variables, 
            configuration=configuration, 
            bridge_id=bridge_ids['generate_test_cases']
            
        )
        print(Testcases)

        # Parse and save test cases to database
        saved_testcases = await parse_and_save_testcases(Testcases, bridge_id)
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": f"Test cases generated and {len(saved_testcases)} saved successfully",
            "result": Testcases,
            "saved_testcase_ids": saved_testcases
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in generating test cases: "+ str(e)})


async def parse_and_save_testcases(testcases_data, bridge_id: str):
    """
    Process AI-generated test cases (JSON object) and save them to database
    """
    saved_testcase_ids = []
    
    try:
        logger.info(f"Processing testcases data type: {type(testcases_data)}")
        
        # Handle different response formats
        if isinstance(testcases_data, dict):
            # If it's a dict, look for common keys that might contain the test cases
            if 'test_cases' in testcases_data:
                test_cases = testcases_data['test_cases']
            elif 'testcases' in testcases_data:
                test_cases = testcases_data['testcases']
            elif 'cases' in testcases_data:
                test_cases = testcases_data['cases']
            elif 'data' in testcases_data:
                test_cases = testcases_data['data']
            else:
                # If no specific key, assume the whole dict is the test cases structure
                test_cases = testcases_data
        elif isinstance(testcases_data, list):
            # If it's already a list, use it directly
            test_cases = testcases_data
        else:
            logger.error(f"Unexpected testcases data format: {type(testcases_data)}")
            return saved_testcase_ids
        
        # If test_cases is a dict with numbered keys, convert to list
        if isinstance(test_cases, dict):
            # Check if keys are like "1", "2", "3" etc.
            if all(key.isdigit() for key in test_cases.keys()):
                test_cases = [test_cases[key] for key in sorted(test_cases.keys(), key=int)]
            else:
                # Try to find a list within the dict
                for key, value in test_cases.items():
                    if isinstance(value, list):
                        test_cases = value
                        break
        
        logger.info(f"Found {len(test_cases)} test cases to process")
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                logger.info(f"Processing test case {i}: {test_case}")
                
                # Extract user input and expected output from JSON structure
                user_input = None
                expected_output = None
                
                # Extract based on your exact JSON structure
                if 'UserInput' in test_case:
                    user_input = test_case['UserInput']
                
                if 'ExpectedOutput' in test_case:
                    expected_output = test_case['ExpectedOutput']
                    # Handle cases where ExpectedOutput is a dict (like location_request, current_time)
                    if isinstance(expected_output, dict):
                        # Convert dict to string representation
                        expected_output = str(expected_output)
                
                if user_input and expected_output:
                    # Create testcase data structure
                    testcase_data = {
                        "bridge_id": bridge_id,
                        "conversation": [
                            {
                                "role": "user",
                                "content": str(user_input)
                            }
                        ],
                        "type": "response",
                        "expected": {
                            "response": str(expected_output)
                        },
                        "matching_type": "contains"
                    }
                    
                    # Save to database
                    result = await create_testcase(testcase_data)
                    saved_testcase_ids.append(str(result.inserted_id))
                    
                    logger.info(f"✓ Saved test case {i} with ID: {result.inserted_id}")
                    logger.debug(f"  Input: {str(user_input)[:50]}...")
                    logger.debug(f"  Output: {str(expected_output)[:50]}...")
                    
                else:
                    logger.warning(f"✗ Could not extract user_input/expected_output from test case {i}")
                    logger.warning(f"  Available keys: {list(test_case.keys()) if isinstance(test_case, dict) else 'Not a dict'}")
                    
            except Exception as case_error:
                logger.error(f"Error processing test case {i}: {str(case_error)}")
                continue
                
    except Exception as e:
        logger.error(f"Error processing test cases: {str(e)}")
        raise HTTPException(status_code=500, detail={"success": False, "error": f"Error processing test cases: {str(e)}"})
    
    return saved_testcase_ids