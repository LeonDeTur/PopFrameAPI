from fastapi import APIRouter, HTTPException, Depends, Query

import json
from popframe.method.aglomeration import AgglomerationBuilder
from popframe.method.popuation_frame import PopulationFrame
from popframe.models.region import Region
from typing import Any, Dict

from app.common.models.popframe_models.popframe_models_service import pop_frame_model_service
from app.dependences import geoserver_storage

agglomeration_router = APIRouter(prefix="/agglomeration", tags=["Agglomeration"])

@agglomeration_router.get("/build_agglomeration")
async def get_agglomeration_endpoint(
        region_id: int
):
    try:
        region_model = await pop_frame_model_service.get_model(region_id)
        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations()
        await geoserver_storage.save_gdf_to_geoserver(
            layer=agglomeration_gdf,
            name="popframe",
            region_id=region_id,
            layer_type="agglomerations",
        )
        result = await geoserver_storage.get_layer_from_geoserver(
            region_id=region_id,
            layer_type="agglomerations",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during agglomeration processing: {str(e)}")


@agglomeration_router.get("/evaluate_city_agglomeration_statuss", response_model=Dict[str, Any])
def evaluate_cities_in_agglomeration(
        region_model: Region = Depends(
            pop_frame_model_service.get_model
        )
):
    try:
        frame_method = PopulationFrame(region=region_model)
        gdf_frame = frame_method.build_circle_frame()

        builder = AgglomerationBuilder(region=region_model)
        agglomeration_gdf = builder.get_agglomerations()
        towns_with_status = builder.evaluate_city_agglomeration_status(gdf_frame, agglomeration_gdf)
        result = json.loads(towns_with_status.to_json())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during city evaluation processing: {str(e)}")
