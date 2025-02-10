from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router_territory, router_population, router_frame, router_agglomeration, router_popframe
from app.routers import router_landuse
from app.routers.router_popframe_models import model_calculator_router
from app.common.models.popframe_models.popframe_models_service import pop_frame_model_service
from loguru import logger
import sys

logger.remove()
log_level = "DEBUG"
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS zz}</green> | <level>{level: <8}</level> | <yellow>Line {line: >4} ({file}):</yellow> <b>{message}</b>"
logger.add(sys.stderr, level=log_level, format=log_format, colorize=True, backtrace=True, diagnose=True)
logger.add("file.log", level=log_level, format=log_format, colorize=False, backtrace=True, diagnose=True)


app = FastAPI(
    title="PopFrame API",
    description="API for PopFrame service, handling territory evaluation, population criteria, network frame, and land use data.",
    version="3.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", response_model=dict[str, str])
def read_root():
    return {"message": "Welcome to PopFrame Service"}

app.include_router(model_calculator_router)
# Include routers
app.include_router(router_territory.territory_router)
app.include_router(router_population.population_router)
app.include_router(router_frame.network_router)
app.include_router(router_agglomeration.agglomeration_router)
app.include_router(router_landuse.landuse_router)
app.include_router(router_popframe.popframe_router)
app.include_router(model_calculator_router)

@app.on_event("startup")
async def startup_event():
    await pop_frame_model_service.load_and_cash_all_models()


