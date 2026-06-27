from __future__ import annotations

from api.code_chat_api import router as code_chat_router
from api.code_result_api import router as code_result_router
from api.main import app

app.include_router(code_chat_router)
app.include_router(code_result_router)
