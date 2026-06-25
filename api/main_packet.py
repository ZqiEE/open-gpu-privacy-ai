from __future__ import annotations

from api.main_owned import app
from api.outbox_api import router as outbox_router
from api.parcel_routes import router

app.include_router(router)
app.include_router(outbox_router)
