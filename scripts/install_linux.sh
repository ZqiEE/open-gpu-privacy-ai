#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${AILOVANTA_HOME:-$HOME/ailovanta}"
PORT="${AILOVANTA_PORT:-8000}"

mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ ! -d .git ]; then
  git clone https://github.com/ZqiEE/ailovanta.git .
else
  git pull --ff-only
fi

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p runtime_data

cat > .env.local <<'EOF'
AILOVANTA_ENV=local
AILOVANTA_RATE_LIMIT_ENABLED=true
AILOVANTA_RATE_LIMIT_PER_MINUTE=120
AILOVANTA_RATE_LIMIT_WINDOW_SECONDS=60
AILOVANTA_REQUIRE_NODE_PROOF=true
AILOVANTA_MIN_AVG_TRUST_SCORE=0.75
EOF

cat > run.sh <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$APP_DIR"
. .venv/bin/activate
set -a
[ -f .env.local ] && . .env.local
set +a
uvicorn api.main_release_ready:app --host 0.0.0.0 --port "$PORT"
EOF
chmod +x run.sh

cat > check.sh <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$APP_DIR"
. .venv/bin/activate
python scripts/check_release.py --route-key owned-chat/default
EOF
chmod +x check.sh

echo "Installed to $APP_DIR"
echo "Run: $APP_DIR/run.sh"
echo "Check: $APP_DIR/check.sh"
