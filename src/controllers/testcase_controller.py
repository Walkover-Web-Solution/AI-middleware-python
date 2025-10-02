from fastapi.responses import JSONResponse, Response
from src.db_services.testcase_services import fetch_testcases_history
import traceback
from src.services.cache_service import make_json_serializable

async def get_testcases_history(request, bridge_id):
    """Return testcase runs grouped by version for a given bridge."""
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
