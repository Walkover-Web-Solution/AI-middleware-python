from fastapi import APIRouter, Request, HTTPException
from src.mongoModel.dataForDemoModel import db
router = APIRouter()

# Define the MongoDB collection
services_collection = db["demo_collection"]

@router.post('/')
async def add_data_for_demo_save(request: Request):
    pass
    try:
        body = await request.json()
        name = body.get('name')
        description = body.get('description')
        link = body.get('link')
        img_url = body.get('img_url')

        if not all([name, description, link, img_url]):
            raise HTTPException(status_code=400, detail="All fields (name, description, link, imgurl) are required.")

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
