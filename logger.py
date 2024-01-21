# In logger.py
import logging
import sys

def init_logger(name):
    """
    Initialize and configure a logger with the given name.

    :param name: The name of the logger.
    """

    # # Create a custom logger
    # logger = logging.getLogger(name)

    # # Set root level
    # root_logger = logging.getLogger()
    # root_logger.setLevel(logging.DEBUG)

    # # Set the log level (Change it based on your requirements)
    # logger.setLevel(logging.DEBUG)

    # # Create handlers
    # console_handler = logging.StreamHandler()

    # # Create formatter and add it to the handler
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # console_handler.setFormatter(formatter)

    # Add handlers to the logger
    # logger.addHandler(console_handler)
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))

    return logger