import logging
import os
import sys

current_dir = os.path.dirname(__file__)
log_dir = os.path.join(current_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
error_file = os.path.abspath(os.path.join(log_dir, 'errors.log'))

formatter = logging.Formatter('[%(asctime)s %(name)s] %(levelname)s: %(message)s')
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(formatter)

error_handler = logging.FileHandler(error_file, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)


def new_logger(name, debug=True):
    _logger = logging.getLogger(name)
    _logger.addHandler(default_handler)
    _logger.addHandler(error_handler)
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)
    return _logger
