from __future__ import annotations

from api.apply_api import router as apply_router
from api.artifact_binding_api import router as artifact_binding_router
from api.autonomous_api import router as autonomous_router
from api.cr_api import router as checkpoint_runtime_router
from api.gg_api import router as gg_router
from api.learning_api import router as learning_router
from api.learning_foundation_api import router as learning_foundation_router
from api.learning_gate_api import router as learning_gate_router
from api.main_owned_default import ailovanta_owned_chat_default as _owned_chat_default_route
from api.main_packet import app
from api.model_monitor_api import router as model_monitor_router
from api.node_admission_api import router as node_admission_router
from api.rflow2_api import router as rflow2_router
from api.rflow_api import router as rflow_router
from api.rollback_api import router as rollback_router
from api.route_book_api import router as route_book_router
from api.route_health_api import router as route_health_router
from api.swarm_model_api import router as distributed_model_router
from api.wio_api import router as wio_router

app.include_router(learning_router)
app.include_router(learning_foundation_router)
app.include_router(learning_gate_router)
app.include_router(model_monitor_router)
app.include_router(rollback_router)
app.include_router(autonomous_router)
app.include_router(artifact_binding_router)
app.include_router(apply_router)
app.include_router(rflow_router)
app.include_router(rflow2_router)
app.include_router(gg_router)
app.include_router(route_book_router)
app.include_router(route_health_router)
app.include_router(wio_router)
app.include_router(node_admission_router)
app.include_router(distributed_model_router)
app.include_router(checkpoint_runtime_router)
