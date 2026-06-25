from __future__ import annotations

from api.learning_api import router as learning_router
from api.learning_foundation_api import router as learning_foundation_router
from api.learning_gate_api import router as learning_gate_router
from api.main_packet import app
from api.model_monitor_api import router as model_monitor_router
from api.rollback_api import router as rollback_router

app.include_router(learning_router)
app.include_router(learning_foundation_router)
app.include_router(learning_gate_router)
app.include_router(model_monitor_router)
app.include_router(rollback_router)
