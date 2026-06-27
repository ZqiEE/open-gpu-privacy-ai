from __future__ import annotations

from api.alert_routes import router as alert_router
from api.main_ops_ready import app

app.include_router(alert_router)
