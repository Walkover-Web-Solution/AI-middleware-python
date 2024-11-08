import logging

# logging.basicConfig(format='%(levelname)s - %(message)s')
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),           # Outputs to console
    ]
)
def get_logger() -> logging.Logger:
    logger = logging.getLogger()
    return logger

logger = get_logger()