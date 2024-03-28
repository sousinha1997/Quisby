import logging
import os
from logging.handlers import RotatingFileHandler


def configure_custom_logging():
    home_dir = os.getenv("HOME")
    log_location = home_dir + "/.quisby/logs/"
    log_level = "INFO"

    if not os.path.exists(log_location):
        os.makedirs(log_location)
    log_filename = log_location + "quisby.log"
    print("[ LOG LOCATION : " + log_filename+" ]")
    log_file_max_bytes = 5
    log_backup_count = 3

    # Create a custom logger
    custom_logger = logging.getLogger("quisby_logger")
    custom_logger.setLevel(log_level)

    # Create a rotating file handler
    rotating_handler = RotatingFileHandler(log_filename, maxBytes=log_file_max_bytes * 1024 * 1024,
                                           backupCount=log_backup_count)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    rotating_handler.setFormatter(formatter)

    # Add the rotating file handler to the custom logger
    custom_logger.addHandler(rotating_handler)

    # Create a stream handler and add it to the custom logger
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    custom_logger.addHandler(stream_handler)

    return custom_logger


# Example usage
if __name__ == "__main__":
    custom_logger = configure_custom_logging()

    # Log messages using the custom logger
    custom_logger.debug("This is a debug message")
    custom_logger.info("This is an info message")
    custom_logger.warning("This is a warning message")
    custom_logger.error("This is an error message")
    custom_logger.critical("This is a critical message")
