from typing import Literal

import numpy as np
import geopandas as gpd
import pandas as pd
from popframe.preprocessing.level_filler import LevelFiller

from app.dependences import (
    urban_api_handler,
    transportframe_api_handler,
    http_exception,
    logger
)


class PopFrameModelApiService:
    """Class for external api services data retrieving"""

    #ToDo processing database level changes
    @staticmethod
    async def get_regions() -> list[int]:
        """
        Function retrieves all available regions
        Returns:
            list[int]: list of available regions as int id
        """

        response = await urban_api_handler.get(
            extra_url="/api/v1/all_territories_without_geometry",
            params={
                "parent_id": 12639
            }
        )
        regions_id_list = [i["territory_id"] for i in response]
        return regions_id_list

    @staticmethod
    async def get_territories_population(territories_ids: list[int]) -> pd.DataFrame:
        """
        Function retrieves population data for provided territories
        Args:
            territories_ids (list): list of territories ids
        Returns:
            pd.DataFrame with id and population data
        Raises:
            500, internal error in case population data parsing fails
        """

        population_list = []
        for ter_id in territories_ids:
            response = await urban_api_handler.get(
                extra_url="/api/v1/territory/892/indicator_values",
                params={
                    "territory_id": ter_id,
                    "indicator_value": 1
                }
            )
            population_list.append(response[0]["value"])
        try:
            population_df = pd.DataFrame(
                np.array([territories_ids, population_list]).T,
                columns=["territory_id", "population"]
            )
            population_df = population_df[population_df["population"] > 0].copy()
            return population_df
        except Exception as e:
            logger.error(f"error during population data retrieval {str(e)}")
            raise http_exception(
                status_code=500,
                msg=f"error during population data retrieval",
                _input=[territories_ids, population_list],
                _detail={"Error": str(e)}
            )

    #ToDo rewrite to object api
    @staticmethod
    async def get_matrix_for_region(
            region_id: int,
            graph_type: Literal["car", "walk", "intermodal"]
    ) -> pd.DataFrame:
        """
        Function retrieves matrix for region
        Args:
            region_id (int): region id
            graph_type (Literal["", ""]): graph type
        Returns:
            pd.DataFrame: matrix index-values
        Raises:
            404, not found, got empty matrix
            500, internal error, matrix parsing fails
        """

        response = await transportframe_api_handler.get(
            extra_url=f"{region_id}/get_matrix",
            params={
                "graph_type": graph_type,
            }
        )
        try:
            adj_mx = pd.DataFrame(response['values'], index=response['index'], columns=response['columns'])
        except Exception as e:
            logger.error(f"error during matrix retrieval {str(e)}")
            raise http_exception(
                status_code=500,
                msg=f"error during matrix parsing",
                _input=response,
                _detail={"Error": str(e)}
            )
        if adj_mx.empty:
            logger.warning(f"matrix for region {region_id} is empty")
            raise http_exception(
                status_code=404,
                msg=f"matrix for region {region_id} not found",
                _input=response,
                _detail={}
            )
        return adj_mx

    async def load_and_cash_models(self):
        """
        Functions loads and cashes all available models
        Returns:
            None
        """

        regions_ids_to_process = await self.get_regions()
        for region_id in regions_ids_to_process:
            cities = await urban_api_handler.get(
                extra_url="/api/v1/all_territories",
                params={
                    "parent_id": region_id,
                    "get_all_levels": True,
                    "cities_only": True,
                    "centers_only": True,
                }
            )
            cities_gdf = gpd.GeoDataFrame.from_features(cities, crs=4326)
            population_data_df = await self.get_territories_population(
                territories_ids=cities["territory_id"].to_list(),
            )
            cities_gdf = pd.merge(cities, population_data_df, on="territory_id").reset_index(drop=True)
            level_filler = LevelFiller(towns=cities_gdf)
            towns = level_filler.fill_levels()
            logger.info(f"Loaded cities for region {region_id}")
            matrix = await self.get_matrix_for_region(region_id=region_id, graph_type="car")
            logger.info(f"Loaded matrix for region {region_id}")

