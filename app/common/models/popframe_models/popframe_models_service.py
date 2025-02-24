import asyncio
import json

import geopandas as gpd
import pandas as pd
from loguru import logger
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.method.popuation_frame import PopulationFrame

from popframe.preprocessing.level_filler import LevelFiller
from popframe.models.region import Region
from app.dependences import (
    urban_api_handler,
    http_exception, geoserver_storage,
)
from app.common.storage.models.pop_frame_caching_service import pop_frame_caching_service
from .services.popframe_models_api_service import pop_frame_model_api_service


class PopFrameModelsService:
    """Class for popframe model handling"""

    @staticmethod
    async def create_model(
            region_borders: gpd.GeoDataFrame,
            towns: gpd.GeoDataFrame,
            adj_mx: pd.DataFrame,
            region_id: int,
    ) -> Region:
        """
        Function initialises popframe region model
        Args:
            region_borders (gpd.GeoDataFrame): region borders
            towns (gpd.GeoDataFrame): region towns layer
            adj_mx (pd.DataFrame): adjacency matrix for region from TransportFrame
            region_id (int): region id
        Returns:
            Region: PopFrame regional model
        Raises:
            500, internal error in case model initialization fails
        """

        local_crs = region_borders.estimate_utm_crs()
        try:
            region_model = Region(
                region = region_borders.to_crs(local_crs),
                towns=towns.to_crs(local_crs),
                accessibility_matrix=adj_mx
            )
            return region_model

        except Exception as e:
            raise http_exception(
                status_code=500,
                msg=f"error during PopFrame model initialization with region {region_id}",
                _input={
                    "region": json.loads(region_borders.to_crs(local_crs).to_json()),
                    "cities": json.loads(towns.to_crs(local_crs).to_json()),
                    "adj_mx": adj_mx.to_dict(),
                },
                _detail={"Error": str(e)}
            )

    async def calculate_model(self, region_id: int) -> None:
        """
        Function calculates popframe model for region
        Args:
            region_id (int): region id
        Returns:
            None
        """

        region_borders = await pop_frame_model_api_service.get_region_borders(region_id)
        cities = await urban_api_handler.get(
            endpoint_url="/api/v1/all_territories",
            params={
                "parent_id": region_id,
                "get_all_levels": "true",
                "cities_only": "true",
                "centers_only": "true",
            },
        )
        if len(cities["features"]) < 1:
            logger.info(f"No cities found for region {region_id}")
        cities_gdf = gpd.GeoDataFrame.from_features(cities, crs=4326)
        population_data_df = await pop_frame_model_api_service.get_territories_population(
            territories_ids=cities_gdf["territory_id"].to_list(),
        )
        cities_gdf = pd.merge(
            cities_gdf,
            population_data_df,
            on="territory_id"
        ).reset_index(drop=True)
        cities_gdf.set_index("territory_id", inplace=True)
        level_filler = LevelFiller(towns=cities_gdf)
        towns = level_filler.fill_levels()
        logger.info(f"Loaded cities for region {region_id}")
        matrix = await pop_frame_model_api_service.get_matrix_for_region(region_id=region_id, graph_type="car")
        matrix = matrix.loc[towns.index, towns.index]
        logger.info(f"Loaded matrix for region {region_id}")
        model = await self.create_model(
            region_borders=region_borders,
            towns=towns,
            adj_mx=matrix,
            region_id=region_id,
        )
        await pop_frame_caching_service.cache_model_to_pickle(
            region_model=model,
            region_id=region_id,
        )
        frame_method = PopulationFrame(region=model)
        gdf_frame = frame_method.build_circle_frame()
        builder = AgglomerationBuilder(region=model)
        agglomeration_gdf = builder.get_agglomerations()
        towns_with_status = builder.evaluate_city_agglomeration_status(gdf_frame, agglomeration_gdf)
        await geoserver_storage.save_gdf_to_geoserver(
            layer=agglomeration_gdf,
            name="popframe",
            region_id=region_id,
            layer_type="agglomerations",
        )
        await geoserver_storage.save_gdf_to_geoserver(
            layer=towns_with_status,
            name="popframe",
            region_id=region_id,
            layer_type="cities",
        )
        await geoserver_storage.save_gdf_to_geoserver(
            layer=towns_with_status,
            name="popframe",
            region_id=region_id,
            layer_type="cities",
        )

    async def load_and_cash_all_models(self):
        """
        Functions loads and cashes all available models
        Returns:
            None
        """

        regions_ids_to_process = await pop_frame_model_api_service.get_regions()
        for i in range(0, len(regions_ids_to_process), 5):
            task_list = [
                self.calculate_model(region_id=j) for j in regions_ids_to_process[i:i+5] if j not in (
                    3268, 3138
                )
            ]
            await asyncio.gather(*task_list)

    async def get_model(
            self,
            region_id: int,
    ) -> Region:
        """
        Function gets model for region
        Args:
            region_id (int): region id
        Returns:
            Region: PopFrame regional model
        """

        if await pop_frame_caching_service.check_path(region_id=region_id):
            model = await pop_frame_caching_service.load_cached_model(region_id=region_id)
            return model
        await self.calculate_model(region_id=region_id)
        return await self.get_model(region_id=region_id)

    @staticmethod
    async def get_available_regions() -> list[int]:
        """
        Function gets available models
        Returns:
            list[int]: available models list
        """

        result = await pop_frame_caching_service.get_available_models()
        return result


pop_frame_model_service = PopFrameModelsService()
