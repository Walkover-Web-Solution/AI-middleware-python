import logging
import sys

# logging.basicConfig(format='%(levelname)s - %(message)s')
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    stream=sys.stdout
)
def get_logger() -> logging.Logger:
    """Return the configured application logger instance."""
    logger = logging.getLogger()
    return logger

logger = get_logger()
