from __future__ import annotations

from api.artifact_binding_api import router as artifact_binding_router
from api.core_result_api import router as core_result_router
from api.default_chat_probe_routes import router as default_chat_probe_router
from api.final_gate_routes import router as final_gate_router
from api.foundation_job_api import router as foundation_job_router
from api.foundation_pipeline_api import router as foundation_pipeline_router
from api.foundation_result_api import router as foundation_result_router
from api.learning_foundation_api import router as learning_foundation_router
from api.learning_gate_api import router as learning_gate_router
from api.main_incident_ready import app
from api.model_monitor_api import router as model_monitor_router
from api.result_guard_routes import router as result_guard_router

app.include_router(final_gate_router)
app.include_router(default_chat_probe_router)
app.include_router(result_guard_router)
app.include_router(core_result_router)
app.include_router(foundation_job_router)
app.include_router(foundation_result_router)
app.include_router(foundation_pipeline_router)
app.include_router(learning_foundation_router)
app.include_router(learning_gate_router)
app.include_router(artifact_binding_router)
app.include_router(model_monitor_router)
