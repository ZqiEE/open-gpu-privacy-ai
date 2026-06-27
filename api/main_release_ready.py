from __future__ import annotations

from api.final_gate_routes import router as final_gate_router
from api.main_incident_ready import app

app.include_router(final_gate_router)
