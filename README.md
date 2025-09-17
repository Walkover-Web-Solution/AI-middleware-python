# GTWU AI (Python Backend - FastAPI)

GTWU AI is an open-source project aimed at building intelligent, scalable, and community-driven AI services.  
This repository contains the **Python backend built with FastAPI**, which powers the core APIs.

## 🚀 Features
- Fast and asynchronous API built with FastAPI
- Easy-to-extend modular structure
- Environment-based configuration
- Open for community-driven extensions
- RAG implimention 
- Chatbot implimention

## 🛠️ Installation
```bash
# Clone the repo
git clone https://github.com/Walkover-Web-Solution/AI-middleware-python.git
cd AI-middleware-python

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload