"""日志配置：按天滚动，控制台 + 文件双输出"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler

_configured = False
LOGGER_NAME = "job_ai"


def get_log_dir(app):
    return os.path.join(os.path.dirname(app.root_path), "logs")


def setup_logger(app):
    global _configured
    if _configured:
        return logging.getLogger(LOGGER_NAME)

    log_dir = get_log_dir(app)
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
    )

    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "app.log"), when="midnight", backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(logging.INFO)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console)
    _configured = True
    return logger


def get_logger():
    return logging.getLogger(LOGGER_NAME)
