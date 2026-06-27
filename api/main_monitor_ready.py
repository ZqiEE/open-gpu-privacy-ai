from __future__ import annotations

from api.alert_metrics_routes import router as alert_metrics_router
from api.main_alert_ready import app

app.include_router(alert_metrics_router)
