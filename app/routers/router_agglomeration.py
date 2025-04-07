from fastapi import APIRouter, HTTPException, Depends, Query

import json
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.method.popuation_frame import PopulationFrame
from popframe.models.region import Region
from typing import Any, Dict

from app.common.models.popframe_models.popframe_models_service import pop_frame_model_service
from app.dependences import geoserver_storage
from app.common.storage.geoserver.geoserver_dto import PopFrameGeoserverDTO

agglomeration_router = APIRouter(prefix="/agglomeration", tags=["Agglomeration"])

@agglomeration_router.get("/geoserver/get_href", response_model=list[PopFrameGeoserverDTO])
async def get_href(
        region_id: int
) -> list[PopFrameGeoserverDTO]:
    try:

        agglomeration_check = await geoserver_storage.check_cached_layers(
            region_id=region_id,
            layer_type="agglomerations"
        )
        cities_check = await geoserver_storage.check_cached_layers(
            region_id=region_id,
            layer_type="cities"
        )
        if agglomeration_check and cities_check:
            agglomerations = await geoserver_storage.get_layer_from_geoserver(
                region_id=region_id,
                layer_type="agglomerations",
            )
            cities = await geoserver_storage.get_layer_from_geoserver(
                region_id=region_id,
                layer_type="cities",
            )
            return [agglomerations, cities]
        else:
            await pop_frame_model_service.calculate_model(region_id)
            result = await get_href(region_id)
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during agglomeration processing: {str(e)}")

@agglomeration_router.get("/build_agglomeration")
async def get_agglomeration_endpoint(
        region_id: int,
        time: int=80
):
    try:
        region_model = await pop_frame_model_service.get_model(region_id)
        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations(time=time)
        agglomeration_gdf.to_crs(4326, inplace=True)
        result = json.loads(agglomeration_gdf.to_json())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during agglomeration processing: {str(e)}")


@agglomeration_router.get("/evaluate_city_agglomeration_status", response_model=Dict[str, Any])
async def evaluate_cities_in_agglomeration(
        region_id: int,
        time: int=80
):
    try:
        region_model = await pop_frame_model_service.get_model(region_id)
        frame_method = PopulationFrame(region=region_model)
        gdf_frame = frame_method.build_circle_frame()
        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations(time=time)
        towns_with_status = builder.evaluate_city_agglomeration_status(gdf_frame, agglomeration_gdf)
        towns_with_status.to_crs(4326, inplace=True)
        result = json.loads(towns_with_status.to_json())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during city evaluation processing: {str(e)}")
