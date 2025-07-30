import logging
import sys
from config.settings import settings

def setup_logging():
    logging.basicConfig(
        level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress verbose logs from external libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("caliber") 