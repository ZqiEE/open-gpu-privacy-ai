from __future__ import annotations

from api.main_commercial_ready import app
from api.rate_limit_middleware import install_rate_limit

install_rate_limit(app)
