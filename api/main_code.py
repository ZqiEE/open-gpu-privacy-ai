from __future__ import annotations

from api.adapter_merge_routes import router as adapter_router
from api.admin_guard_middleware import install_admin_guard
from api.artifact_routes import router as artifact_router
from api.artifact_version_routes import router as artifact_version_router
from api.benchmark_routes import router as benchmark_router
from api.catalog_secure_publish import router as csp_router
from api.catalog_routes import router as catalog_router
from api.catalog_extra_routes import router as extra_router
from api.code_chat_api import router as code_chat_router
from api.code_result_api import router as code_result_router
from api.compat_routes import router as compat_router
from api.humaneval_routes import router as humaneval_router
from api.admin_routes import router as admin_router
from api.monitoring_routes import router as monitoring_router
from api.node_key_routes import router as node_key_router
from api.object_store_routes import router as object_store_router
from api.ops_routes import router as ops_router
from api.prometheus_routes import router as prometheus_router
from api.qlora_routes import router as qlora_router
from api.queue_routes import router as queue_router
from api.reputation_routes import router as reputation_router
from api.runtime_extra_routes import router as rt_router
from api.runtime_forward_routes import router as fw_router
from api.scheduler_routes import router as scheduler_router
from api.strong_benchmark_routes import router as strong_benchmark_router
from api.main import app

install_admin_guard(app)

app.include_router(code_chat_router)
app.include_router(code_result_router)
app.include_router(csp_router)
app.include_router(catalog_router)
app.include_router(extra_router)
app.include_router(rt_router)
app.include_router(benchmark_router)
app.include_router(fw_router)
app.include_router(compat_router)
app.include_router(strong_benchmark_router)
app.include_router(adapter_router)
app.include_router(artifact_router)
app.include_router(humaneval_router)
app.include_router(node_key_router)
app.include_router(object_store_router)
app.include_router(qlora_router)
app.include_router(ops_router)
app.include_router(monitoring_router)
app.include_router(queue_router)
app.include_router(reputation_router)
app.include_router(artifact_version_router)
app.include_router(admin_router)
app.include_router(prometheus_router)
app.include_router(scheduler_router)
