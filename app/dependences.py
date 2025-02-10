from datetime import datetime

from iduconfig import Config
from loguru import logger

from app.common.api_handler.api_handler import APIHandler
from app.common.exceptions.http_exception_wrapper import http_exception


config = Config()

logger.add(
    f"{config.get('LOGS_DIR')}/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log",
    format="<green>{time:MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}.{function}</cyan> - "
    "<level>{message}</level>",
)


urban_api_handler = APIHandler(config.get("URBAN_API"))
transportframe_api_handler = APIHandler(config.get("TRANSPORTFRAME_API"))
