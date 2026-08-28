"""Background worker that receives simulator data and feeds the ingestor."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.services.telemetry import telemetry_ingestor

logger = logging.getLogger(__name__)
SIMULATOR_URL = "http://localhost:8001"


class SimulatorBridge:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        import os
        if os.getenv("SKIP_SIMULATOR", "").lower() in ("1", "true", "yes"):
            logger.info("Simulator bridge disabled (SKIP_SIMULATOR=1)")
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Simulator bridge started — polling %s", SIMULATOR_URL)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def _poll_loop(self) -> None:
        await asyncio.sleep(3)
        async with httpx.AsyncClient(timeout=10.0) as client:
            while self._running:
                try:
                    resp = await client.get(f"{SIMULATOR_URL}/readings")
                    if resp.status_code == 200:
                        readings = resp.json()
                        if readings:
                            await telemetry_ingestor.ingest_batch(readings)
                except httpx.ConnectError:
                    logger.debug("Simulator not yet available")
                except Exception as e:
                    logger.warning("Simulator poll error: %s", e)
                await asyncio.sleep(15)


simulator_bridge = SimulatorBridge()
