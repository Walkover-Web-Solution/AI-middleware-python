# Controller Function
from fastapi.responses import JSONResponse, Response
from src.db_services.templateDbservice import get_template
import json
from datetime import datetime
from bson import ObjectId

# Custom JSON encoder to handle MongoDB data types
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def serialize_mongo_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    
    if isinstance(doc, dict):
        return {k: serialize_mongo_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    elif isinstance(doc, datetime):
        return doc.isoformat()
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

async def return_template(request, template_id):
    try:
        # Get template data from database service
        data = await get_template(template_id)
        
        # Handle case where template is not found
        if not data:
            return JSONResponse(
                status_code=404, 
                content={"status": "error", "message": f"Template with ID {template_id} not found"}
            )
        
        # Serialize MongoDB document to make it JSON compatible
        serialized_data = serialize_mongo_doc(data)
            
        return JSONResponse(content={"status": "success", "data": serialized_data})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to retrieve template data"}
        )
