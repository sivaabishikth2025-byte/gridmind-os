import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, engine
from app.services.simulator_bridge import simulator_bridge
from app.services.telemetry import telemetry_ingestor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

    await telemetry_ingestor.start()
    await simulator_bridge.start()
    logger.info("GridMind OS backend ready")

    yield

    await simulator_bridge.stop()
    await telemetry_ingestor.stop()
    await engine.dispose()


app = FastAPI(
    title="GridMind OS",
    description="Autonomous AI-Powered Grid Optimization Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)
