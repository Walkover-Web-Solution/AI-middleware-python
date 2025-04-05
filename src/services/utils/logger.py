import logging
import sys
import json

class GCPFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "message": record.getMessage(),
            "severity": record.levelname  # Critical for GCP to assign correct severity
        }
        return json.dumps(log_data)

def get_logger() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove any default handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(GCPFormatter())
    logger.addHandler(handler)
    return logger

logger = get_logger()