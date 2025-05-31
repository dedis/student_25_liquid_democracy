import logging
from datetime import datetime
import os
from typing import Tuple

def create_logger(name_prefix="log", level=logging.INFO, folder="logs") -> Tuple[logging.Logger, logging.Handler]:
    """
    Creates a logger that writes to a uniquely named file in a specified folder.

    Examlple usage:
        
        logger, handler = logger_creator.create_logger(name_prefix="iterative")
        logger.info(f"Iterated {count} times ({len(nodes)} nodes)")
        logger.removeHandler(handler)
        handler.close()
    
    Args:
        name_prefix (str): Prefix for the filename.
        level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
        folder (str): Folder where log files will be saved.

    Returns:
        logger (logging.Logger): Configured logger object.
        handler (logging.Handler): The file handler (for manual cleanup).
    """

    # Get the name of the script that is running
    log_folder = f"log"
    
    # Make sure the folder exists (relative to script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_log_folder = os.path.join(script_dir, log_folder)
    os.makedirs(full_log_folder, exist_ok=True)

    # Create the log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    logger_name = f"{name_prefix}_{timestamp}"
    log_filepath = os.path.join(full_log_folder, f"{logger_name}.log")
    
    # Set up the logger
    logger = logging.getLogger(logger_name)
    handler = logging.FileHandler(log_filepath)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # Avoid double logging

    return logger, handler
