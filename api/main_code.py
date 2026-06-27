from __future__ import annotations

from api.catalog_routes import router as catalog_router
from api.catalog_extra_routes import router as extra_router
from api.code_chat_api import router as code_chat_router
from api.code_result_api import router as code_result_router
from api.runtime_extra_routes import router as rt_router
from api.main import app

app.include_router(code_chat_router)
app.include_router(code_result_router)
app.include_router(catalog_router)
app.include_router(extra_router)
app.include_router(rt_router)
