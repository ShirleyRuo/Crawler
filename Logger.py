import sys

import logging
from pathlib import Path

class Logger:

    def __init__(self, log_dir : Path) -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(exist_ok=True)
    
    def get_logger(
            self, 
            module_name : str,
            log_level : logging._Level = logging.DEBUG
            ) -> logging.Logger:
        logger = logging.getLogger(module_name)
        logger.setLevel(level=log_level)

        if len(logger.handlers) == 2 and isinstance(logger.handlers[0], logging.FileHandler) and isinstance(logger.handlers[1], logging.StreamHandler):
            return logger

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(self._log_dir / f'{module_name}.log', mode='a')
        file_handler.setLevel(level=log_level)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level=log_level)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        return logger