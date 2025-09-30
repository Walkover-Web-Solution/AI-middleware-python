from fastapi.responses import JSONResponse, Response
from src.db_services.testcase_services import (
    fetch_testcases_history, 
    create_testcase, 
    delete_testcase_by_id, 
    get_all_testcases_by_bridge_id
)
import traceback
from src.services.cache_service import make_json_serializable

async def get_testcases_history(request, bridge_id):
    try:
        testcases = await fetch_testcases_history(bridge_id)
        for testcase in testcases: 
            testcase['version_history'] = {}
            for history in testcase['history']:
                if not testcase['version_history'].get(history['version_id']):
                    testcase['version_history'][history['version_id']] = []
                testcase['version_history'][history['version_id']].append(history)
            del testcase['history']
            
        return JSONResponse(content = {
            "success": True,
            "data" : make_json_serializable(testcases)
        })
    except Exception as error :
        traceback.print_exc()
        return JSONResponse(status_code = 400, content = {
            "success": False,
            "error": str(error)
        })

async def create_testcase_controller(request):
    """Create a new testcase"""
    try:
        body = await request.json()
        
        # Validate required fields
        required_fields = ['bridge_id', 'conversation', 'type', 'expected', 'matching_type']
        for field in required_fields:
            if field not in body:
                return JSONResponse(status_code=400, content={
                    "success": False,
                    "error": f"Missing required field: {field}"
                })
        
        result = await create_testcase(body)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "_id": str(result.inserted_id),
                "message": "Testcase created successfully"
            }
        })
    except Exception as error:
        traceback.print_exc()
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": str(error)
        })

async def delete_testcase_controller(testcase_id):
    """Delete a testcase by _id"""
    try:
        result = await delete_testcase_by_id(testcase_id)
        
        if result.deleted_count == 0:
            return JSONResponse(status_code=404, content={
                "success": False,
                "error": "Testcase not found"
            })
        
        return JSONResponse(content={
            "success": True,
            "message": "Testcase deleted successfully"
        })
    except Exception as error:
        traceback.print_exc()
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": str(error)
        })

async def get_all_testcases_controller(bridge_id):
    """Get all testcases for a specific bridge_id"""
    try:
        testcases = await get_all_testcases_by_bridge_id(bridge_id)
        
        return JSONResponse(content={
            "success": True,
            "data": make_json_serializable(testcases)
        })
    except Exception as error:
        traceback.print_exc()
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": str(error)
        })