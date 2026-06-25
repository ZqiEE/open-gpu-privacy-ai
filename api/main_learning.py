from __future__ import annotations

from api.learning_api import router as learning_router
from api.learning_foundation_api import router as learning_foundation_router
from api.main_packet import app

app.include_router(learning_router)
app.include_router(learning_foundation_router)
