from fastapi import APIRouter, Request, HTTPException
from src.mongoModel.dataForDemoModel import db
router = APIRouter()
import json
from google.cloud import storage
from google.oauth2 import service_account
from config import Config
import uuid
from bson import ObjectId
services_collection = db["demo_collection"]

@router.post('/')
async def add_data_for_demo_save(request: Request):
    try:
        body = await request.form()
        image = body.get('image')
        name = body.get('name')
        description = body.get('description')
        link = body.get('link')

        if not all([image, name, description, link]):
            raise HTTPException(status_code=400, detail="All fields (name, description, link, image) are required.")
        
        # Process image upload
        file_content = await image.read()
        
        # Set up Google Cloud Storage client
        credentials_dict = json.loads(Config.GCP_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = storage.Client(credentials=credentials)
        
        # Upload image and get URL
        bucket = storage_client.bucket('ai_middleware_testing')
        filename = f"showcase/{uuid.uuid4()}_{image.filename}"
        blob = bucket.blob(filename)
        blob.upload_from_string(file_content, content_type=image.content_type)
        img_url = f"https://storage.googleapis.com/ai_middleware_testing/{filename}"

        # Prepare the document to insert into the MongoDB collection
        service_document = {
            "name": name,
            "description": description,
            "link": link,
            "img_url": img_url
        }

        # Insert the document into the MongoDB collection
        result = services_collection.insert_one(service_document)

        return {
            'success': True,
            'data': {
                'id': str(result.inserted_id),
                'name': name,
                'description': description,
                'link': link,
                'imgurl': img_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/')
async def get_all_data_for_demo(request: Request):
    try:
        documents = services_collection.find()
        data_list = []
        for document in documents:
            document['_id'] = str(document['_id'])  # Convert ObjectId to string
            data_list.append(document)
        return {
            'success': True,
            'data': data_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/{id}')
async def update_data_for_demo(request: Request, id: str):
    try:
        # Get form data
        form = await request.form()
        name = form.get('name')
        description = form.get('description')
        link = form.get('link')
        image = form.get('image')

        # Get existing document
        existing_doc = services_collection.find_one({'_id': ObjectId(id)})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        update_data = {}
        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description
        if link:
            update_data['link'] = link

        # Handle image upload if provided
        if image:
            file_content = await image.read()
            
            # Set up GCP client
            credentials_dict = json.loads(Config.GCP_CREDENTIALS)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            storage_client = storage.Client(credentials=credentials)
            
            # Upload new image
            bucket = storage_client.bucket('ai_middleware_testing')
            filename = f"showcase/{uuid.uuid4()}_{image.filename}"
            blob = bucket.blob(filename)
            blob.upload_from_string(file_content, content_type=image.content_type)
            img_url = f"https://storage.googleapis.com/ai_middleware_testing/{filename}"
            
            update_data['img_url'] = img_url

        if update_data:
            # Update document
            result = services_collection.update_one(
                {'_id': ObjectId(id)},
                {'$set': update_data}
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Update failed")

            # Get updated document
            updated_doc = services_collection.find_one({'_id': ObjectId(id)})
            updated_doc['_id'] = str(updated_doc['_id'])

            return {
                'success': True,
                'data': updated_doc
            }
        else:
            raise HTTPException(status_code=400, detail="No fields to update")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
