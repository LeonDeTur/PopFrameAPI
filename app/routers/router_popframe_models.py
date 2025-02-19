from fastapi import APIRouter
from loguru import logger

from app.common.models.popframe_models.popframe_models_service import pop_frame_model_service


model_calculator_router = APIRouter(prefix="/model_calculator")


@model_calculator_router.put("/recalculate/{region_id}")
async def recalculate_region(region_id: int):
    """Router recalculates model for region"""

    await pop_frame_model_service.calculate_model(region_id)
    logger.info(f"Successfully calculated model for region with id {region_id}")
    return {"msg": f"successfully calculated model for region with id {region_id}"}

@model_calculator_router.get("/available_regions")
async def get_available_regions():
    """Router returns calculated and cached models"""

    return await pop_frame_model_service.get_available_regions()
