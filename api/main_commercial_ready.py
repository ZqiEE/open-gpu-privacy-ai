from __future__ import annotations

from api.main_runtime_ready import app
from api.prod_ready_plus_routes import router as prod_ready_plus_router

app.include_router(prod_ready_plus_router)
