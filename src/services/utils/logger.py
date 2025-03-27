import logging
import sys
# logging.basicConfig(format='%(levelname)s - %(message)s')
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),           # Outputs to console
    ]
)
def get_logger() -> logging.Logger:
    logger = logging.getLogger()
    return logger

logger = get_logger()