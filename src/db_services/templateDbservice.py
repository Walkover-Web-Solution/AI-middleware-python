# Database Service Function
from models.mongo_connection import db
from bson import ObjectId

configurationModel = db["templates"]

async def get_template(template_id: str):
    """Retrieve a template document, accepting either string or ObjectId inputs."""
    try:
        # Handle potential ObjectId conversion if your template_id is stored as ObjectId
        template_query = {"_id": template_id}

        # Try to convert to ObjectId if it's in that format
        try:
            if ObjectId.is_valid(template_id):
                template_query = {"_id": ObjectId(template_id)}
        except:
            # If conversion fails, keep the original string ID
            pass

        document = await configurationModel.find_one(template_query)

        if not document:
            return None

        return document

    except Exception as e:
        raise
