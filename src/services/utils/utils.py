from fastapi.responses import JSONResponse
from models.mongo_connection import db as mongo_db
from models.index import combined_models as models
from src.services.cache_service import client as redis_client
import sqlalchemy as sa 

pg = models['pg']



async def healthcheck():
    health_status = {
        "status": "OK running good... v1.2",
        "database_status": {
            "mongodb": "disconnected",
            "postgres": "disconnected", 
            "redis": "disconnected"
        }
    }

    # Check MongoDB connection
    try:
        await mongo_db.command('ping')
        health_status["database_status"]["mongodb"] = "connected"
    except Exception as e:
        health_status["database_status"]["mongodb"] = f"error: {str(e)}"

    # Check Postgres connection  
    try:
         # Ensure sa is defined
        session = pg['session']()
        session.execute(sa.text("SELECT 1"))
        session.commit()
        health_status["database_status"]["postgres"] = "connected"
    except Exception as e:
        health_status["database_status"]["postgres"] = f"error: {str(e)}"
    finally:
        session.close()

    # Check Redis connection
    try:
        await redis_client.ping()
        health_status["database_status"]["redis"] = "connected"
    except Exception as e:
        health_status["database_status"]["redis"] = f"error: {str(e)}"
    

    return JSONResponse(status_code=200, content=health_status)