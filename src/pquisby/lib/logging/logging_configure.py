import logging
import os
from logging.handlers import RotatingFileHandler

home_dir = os.getenv("HOME")
log_location = home_dir + "/.pquisby/"

def configure_logging():

    log_level = "INFO"
    if not os.path.exists(log_location):
        os.makedirs(log_location)
    log_filename = log_location+"pquisby.log"
    log_file_max_bytes = 5
    log_backup_count = 3

    # Create a rotating file handler
    rotating_handler = RotatingFileHandler(log_filename, maxBytes=log_file_max_bytes * 1024 * 1024, backupCount=log_backup_count)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    rotating_handler.setFormatter(formatter)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            rotating_handler
        ]
    )
