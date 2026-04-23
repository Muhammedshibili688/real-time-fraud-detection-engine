import logging
import os, sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Defining log Constants
LOG_DIR = "logs"
LOG_FILE = f"{datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Construct LOG_FILE Path
# 2. Path Logic (Ensures logs folder is at the project root)
# Since this file is in src/logger/, we go two levels up to find roo
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
LOG_DIR_PATH = os.path.join(PROJECT_ROOT, LOG_DIR)

# Create the logs directory if it doesn't exist
os.makedirs(LOG_DIR_PATH, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR_PATH, LOG_FILE)

# Logger Configuration
def logger_config():

    # Get Root Logger and attach handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)

    """
    Sets up the global logging configuration.
    - Info and higher goes to the console.
    - Debug and higher goes to the rotating file.
    """
    # Create Formatter
    formatter = logging.Formatter("[ %(asctime)s ] - %(name)s - %(levelname)s - %(message)s")

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, 
        maxBytes=MAX_LOG_SIZE, 
        backupCount=BACKUP_COUNT, 
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logging.getLogger().addHandler(file_handler)

    # Avoid duplicate handlers if script is re-run
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

# 3. Trigger configuration immediately upon import
logger_config()