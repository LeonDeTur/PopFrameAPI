from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks, Request
import json
import geopandas as gpd
from typing import Any, Dict
from popframe.method.landuse_assessment import LandUseAssessment
from popframe.models.region import Region
from app.common.models.popframe_models.popframe_models_service import pop_frame_model_service
from app.dependences import config
from app.utils.auth import verify_token
import requests

landuse_router = APIRouter(prefix="/landuse", tags=["Landuse data"])

# Land Use Data Endpoints
@landuse_router.post("/get_landuse_data", response_model=Dict[str, Any])
async def get_landuse_data_endpoint(
    region_model: Region = Depends(pop_frame_model_service.get_model),
    project_scenario_id: int | None = Query(None, description="ID сценария cценария"),
    token: str = Depends(verify_token)
    ):
    try:
        # Getting project_id and additional information based on scenario_id
        scenario_response = requests.get(
            f"{config.get('URBAN_API')}/scenarios/{project_scenario_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if scenario_response.status_code != 200:
            raise Exception("Error retrieving scenario information")

        scenario_data = scenario_response.json()
        project_id = scenario_data.get("project", {}).get("project_id")
        if project_id is None:
            raise Exception("Project ID is missing in scenario data.")

        # Retrieving territory geometry
        territory_response = requests.get(
            f"{config.get('URBAN_API')}/projects/{project_id}/territory",
            headers={"Authorization": f"Bearer {token}"}
        )
        if territory_response.status_code != 200:
            raise Exception("Error retrieving territory geometry")

        # Extracting only the polygon geometry
        territory_data = territory_response.json()
        territory_geometry = territory_data["geometry"]

        # Converting the territory geometry to GeoDataFrame
        territory_feature = {
            'type': 'Feature',
            'geometry': territory_geometry,
            'properties': {}
        }
        urbanisation = LandUseAssessment(region=region_model)
        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=4326)
        landuse_data = urbanisation.get_landuse_data(territories=polygon_gdf)
        return json.loads(landuse_data.to_json())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

