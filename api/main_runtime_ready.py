from __future__ import annotations

from api.main_code_plus import app
from api.runtime_route_readiness import router as runtime_route_readiness_router

app.include_router(runtime_route_readiness_router)
