import io
import PyPDF2
import docx
import pandas as pd
from fastapi import UploadFile, File


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