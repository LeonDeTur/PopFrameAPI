import asyncio
from pathlib import Path

from popframe.models.region import Region

from app.dependences import logger, http_exception, config
from .caching_serivce import CachingService

class PopFrameCachingService(CachingService):
    """Popframe model caching service"""

    def __init(self, popframe_cache_path: Path):

        super().__init__(popframe_cache_path)

    async def cache_model_to_pickle(self, region_model: Region, region_id: int) -> str:
        """
        Function caches popframe model to pickle
        Args:
            region_model (Region): popframe region model to cache
            region_id (int): region id
        Returns:
            None
        """

        string_path = self.caching_path.joinpath(".".join([str(region_id), "pkl"])).__str__()
        try:
            await asyncio.to_thread(
                region_model.to_pickle,
                string_path
            )
            logger.info(f"Cached file {region_id} to {string_path}")
        except Exception as e:
            raise http_exception(
                status_code=500,
                msg=f"Failed to cache file to pickle {region_id}",
                _input={"region": region_model.__str__()},
                _detail={"Error": str(e)}
            )

    async def load_cached_model(
            self,
            region_id: int
    ):
        """
        Function loads model from cache
        Args:
            region_id (int): region id
        Returns:
            Region: popframe region model
        Raises:
            500, Error during model loading
        """

        model_to_load = self.caching_path.joinpath(".".join([str(region_id), "pkl"])).__str__()
        try:
            model = await asyncio.to_thread(Region.from_pickle, model_to_load)
            logger.info(f"Loaded file {region_id} to {model_to_load}")
            return model
        except Exception as e:
            raise http_exception(
                status_code=500,
                msg=f"Failed to load file from pickle {region_id}",
                _input={"filepath": model_to_load},
                _detail={"Error": str(e)}
            )


pop_frame_caching_service = PopFrameCachingService(
    Path().absolute() / config.get("POPFRAME_MODEL_CACHE")
)
