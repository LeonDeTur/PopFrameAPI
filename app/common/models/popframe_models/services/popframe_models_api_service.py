import asyncio
from typing import Literal

import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from loguru import logger

from app.dependences import (
    urban_api_handler,
    transportframe_api_handler,
    http_exception,
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
            endpoint_url="/api/v1/all_territories_without_geometry",
            params={
                "parent_id": 12639
            }
        )
        regions_id_list = [i["territory_id"] for i in response]
        return regions_id_list

    @staticmethod
    async def get_region_borders(
            region_id: int,
    ) -> gpd.GeoDataFrame:
        """
        Function retrieves region borders based on region id
        Args:
            region_id (int): region id in urban db
        Returns:
            gpd.GeoDataFrame: region borders
        Raises:
            500, error during geometry parsing,
            Any, error from urban api
        """

        response = await urban_api_handler.get(
            endpoint_url=f"/api/v1/territory/{region_id}",
        )
        try:
            region_borders = gpd.GeoDataFrame(
                geometry=[shape(response["geometry"])],
                crs=4326
            )
            return region_borders
        except Exception as e:
            raise http_exception(
                status_code=500,
                msg=f"Error geometry parsing for borders of region {region_id}",
                _input=response["geometry"],
                _detail={
                    "Error": str(e),
                }
            )

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
        for item in range(0, len(territories_ids), 15):
            current_ids = territories_ids[item: item + 15]
            task_list = [
                urban_api_handler.get(
                    endpoint_url=f"/api/v1/territory/{ter_id}/indicator_values",
                    params={
                        "indicator_value": 1
                    }
                ) for ter_id in current_ids
            ]
            results = await asyncio.gather(*task_list)
            logger.info(f"Population response length: {len(results)}")
            pop_to_add = [i[0]["value"] if len(i) > 0 else 0 for i in results]
            population_list += pop_to_add
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
            endpoint_url=f"/{region_id}/get_matrix",
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

pop_frame_model_api_service = PopFrameModelApiService()
