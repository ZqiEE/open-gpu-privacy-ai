from __future__ import annotations

from api.default_chat_probe_routes import router as default_chat_probe_router
from api.main_release_ready import app

app.include_router(default_chat_probe_router)
