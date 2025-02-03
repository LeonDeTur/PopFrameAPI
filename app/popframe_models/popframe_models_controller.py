from fastapi import APIRouter

from app.dependences import logger
from .popframe_models_service import pop_frame_model_service


model_calculator_router = APIRouter(prefix="/model_calculator")


@model_calculator_router.put("/recalculate/{region_id}")
async def recalculate_region(region_id: int):
    """Router recalculates model for region"""

    await pop_frame_model_service.calculate_model(region_id)
    logger.info(f"Successfully calculated model for region with id {region_id}")
    return {"msg": f"successfully calculated model for region with id {region_id}"}
