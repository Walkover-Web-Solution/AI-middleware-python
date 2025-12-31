from models.mongo_connection import db

def get_template_by_id(template_id):
    """
    Fetch a template by its ID from the rich_ui_templates collection.
    """
    try:
        collection = db['rich_ui_templates']
        template = collection.find_one({"_id": template_id})
        return template
    except Exception as e:
        print(f"Error fetching template: {e}")
        return None
