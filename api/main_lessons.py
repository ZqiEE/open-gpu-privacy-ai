from __future__ import annotations

from api.lesson_api import router as lesson_router
from api.main_learning import app

app.include_router(lesson_router)
