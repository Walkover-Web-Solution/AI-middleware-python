from models.mongo_connection import db
from typing import Optional, Dict, Any
import traceback
from bson import ObjectId

response_template_db = db['rich_ui_templates']

async def get_response_template_by_id(template_id: str, org_id: str = 'default_org') -> Optional[Dict[str, Any]]:
    """
    Retrieve a response template by template_id from the database
    
    Args:
        template_id (str): Template ID to retrieve (ObjectId string)
        org_id (str): Organization ID (defaults to 'default_org')
        
    Returns:
        Optional[Dict[str, Any]]: Template data or None if not found
    """
    try:
        # Convert template_id to ObjectId format
        try:
            object_id = ObjectId(template_id)
        except Exception:
            # Invalid ObjectId format
            return None
            
        query = {"_id": object_id}
        
        template = await response_template_db.find_one(query)
        
        if template:
            # Convert ObjectId to string to avoid JSON serialization issues
            clean_template = {}
            for key, value in template.items():
                if key == '_id':
                    clean_template[key] = str(value)
                else:
                    clean_template[key] = value
            return clean_template.get('template_data', clean_template)
        
        return None
        
    except Exception as e:
        print(f"Error fetching response template: {str(e)}")
        traceback.print_exc()
        return None

async def get_multiple_response_templates(template_ids: list, org_id: str = 'default_org') -> Dict[str, Any]:
    """
    Retrieve multiple response templates by template_ids from the database
    
    Args:
        template_ids (list): List of template IDs to retrieve
        org_id (str): Organization ID (defaults to 'default_org')
        
    Returns:
        Dict[str, Any]: Dictionary with template_id as key and template_data as value
    """
    try:
        # Convert template_ids to ObjectId format
        object_ids = []
        for tid in template_ids:
            try:
                object_ids.append(ObjectId(tid))
            except Exception:
                # Skip invalid ObjectId strings
                continue
        
        query = {
            "_id": {"$in": object_ids}, 
        }
        
        cursor = response_template_db.find(query)
        templates = await cursor.to_list(length=None)
        
        # Convert to dictionary format using _id as key and handle ObjectId serialization
        template_dict = {}
        for template in templates:
            # Convert ObjectId to string to avoid JSON serialization issues
            clean_template = {}
            for key, value in template.items():
                if key == '_id':
                    clean_template[key] = str(value)
                else:
                    clean_template[key] = value
            template_dict[str(template['_id'])] = clean_template
        
        return template_dict
        
    except Exception as e:
        print(f"Error fetching multiple response templates: {str(e)}")
        traceback.print_exc()
        return {}

# Fallback templates for when database is not available or templates are not found
FALLBACK_TEMPLATES = {
    "template_1": {
        "type": "Card",
        "children": [
            {
                "type": "Col",
                "align": "center",
                "gap": 4,
                "padding": 4,
                "children": [
                    {
                        "type": "Box",
                        "background": "green-400",
                        "radius": "full",
                        "padding": 3,
                        "children": [
                            {
                                "type": "Icon",
                                "name": "check",
                                "size": "3xl",
                                "color": "white"
                            }
                        ]
                    },
                    {
                        "type": "Col",
                        "align": "center",
                        "gap": 1,
                        "children": [
                            {
                                "type": "Title",
                                "value": "Enable notification"
                            },
                            {
                                "type": "Text",
                                "value": "Notify me when this item ships",
                                "color": "secondary"
                            }
                        ]
                    }
                ]
            },
            {
                "type": "Row",
                "children": [
                    {
                        "type": "Button",
                        "label": "Yes",
                        "block": True,
                        "onClickAction": {
                            "type": "notification.settings",
                            "payload": {
                                "enable": True
                            }
                        }
                    },
                    {
                        "type": "Button",
                        "label": "No",
                        "block": True,
                        "variant": "outline",
                        "onClickAction": {
                            "type": "notification.settings",
                            "payload": {
                                "enable": False
                            }
                        }
                    }
                ]
            }
        ]
    },
    "template_2": {
        "type": "Card",
        "size": "lg",
        "confirm": {
            "action": {
                "type": "email.send"
            },
            "label": "Send email"
        },
        "cancel": {
            "action": {
                "type": "email.discard"
            },
            "label": "Discard"
        },
        "children": [
            {
                "type": "Row",
                "children": [
                    {
                        "type": "Text",
                        "value": "FROM",
                        "width": 80,
                        "weight": "semibold",
                        "color": "tertiary",
                        "size": "xs"
                    },
                    {
                        "type": "Text",
                        "value": "zj@openai.com",
                        "color": "tertiary"
                    }
                ]
            }
        ]
    }
}
