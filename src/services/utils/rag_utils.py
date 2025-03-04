import io
import PyPDF2
import docx
import pandas as pd
from fastapi import UploadFile, File
from .apiservice import fetch
import json

async def extract_pdf_text(file: UploadFile) -> str:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(await file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from DOCX file
async def extract_docx_text(file: UploadFile) -> str:
    doc = docx.Document(io.BytesIO(await file.read()))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to extract text from CSV file
async def extract_csv_text(file: UploadFile) -> str:
    df = pd.read_csv(io.BytesIO(await file.read()))
    def row_to_string(row):
        return ', '.join([f"{col}: {value}" for col, value in row.items()])

    data = df.apply(row_to_string, axis=1).tolist()
    return data

async def get_csv_query_type(doc_data, query):
    content = doc_data.get('content', {})
    
    if not {'rowWiseData', 'columnWiseData'}.issubset(content):
        return 'rowWiseData' if 'rowWiseData' in content else 'columnWiseData'
    
    response, _ = await fetch(
        url='https://api.gtwy.ai/api/v2/model/chat/completion', 
        method='POST',
        headers={'pauthkey': '1b13a7a038ce616635899a239771044c'},
        json_body={
            'user': 'Hello',
            'variables': {'headers' : doc_data['content']['headers'], 'query' : query},
            'bridge_id': '67c2f4b40ef03932ed9a2b40'
        }
    )
    
    query_type = json.loads(response['response']['data']['content'])['search']
    return 'columnWiseData' if query_type == 'column' else 'rowWiseData'
    
    