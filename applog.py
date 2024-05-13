import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler

# Configure Logger
logger = logging.getLogger("App")
logger.setLevel(logging.DEBUG)

# Set up concurrent log handler
log_filename = './log/app.log'
# log rotation will automatically create a new log file when the current log 
# file reaches a certain size (512 KB in this example).
# Once the number of log files exceeds the specified maximum (100 in this example), 
# the oldest file will be deleted to make room for a new file.
rotate_handler = ConcurrentRotatingFileHandler(log_filename, "a", 512*1024, 100)
formatter = logging.Formatter('%(asctime)s - %(levelname)s  - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
rotate_handler.setFormatter(formatter)

logger.addHandler(rotate_handler)