import logging

logging.basicConfig(format='%(levelname)s - %(message)s')
def get_logger() -> logging.Logger:
    logger = logging.getLogger()
    return logger

logger = get_logger()
