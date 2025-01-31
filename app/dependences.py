from iduconfig import Config
from loguru import logger

from app.common.api_handler.api_handler import APIHandler
from app.common.exceptions.http_exception_wrapper import http_exception

config = Config()
urban_api_handler = APIHandler(config.get("URBAN_API"))
transportframe_api_handler = APIHandler(config.get("TRANSPORTFRAME_API"))
