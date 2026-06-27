#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ailovanta}"
REPO_URL="${REPO_URL:-https://github.com/ZqiEE/ailovanta.git}"

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx curl

if [ ! -d "$APP_DIR/.git" ]; then
  sudo mkdir -p "$APP_DIR"
  sudo chown "$USER":"$USER" "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull
fi

cd "$APP_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo mkdir -p /etc/ailovanta
if [ ! -f /etc/ailovanta/ailovanta.env ]; then
  sudo cp deploy/env.example /etc/ailovanta/ailovanta.env
fi

sudo cp deploy/systemd/api.service /etc/systemd/system/ailovanta-api.service
sudo cp deploy/systemd/runtime.service /etc/systemd/system/ailovanta-runtime.service
sudo systemctl daemon-reload
sudo systemctl enable ailovanta-api
sudo systemctl enable ailovanta-runtime
sudo systemctl restart ailovanta-api
sudo systemctl restart ailovanta-runtime

echo "Ailovanta API: http://127.0.0.1:8000"
echo "Ailovanta Runtime: http://127.0.0.1:9001"
echo "Edit /etc/ailovanta/ailovanta.env before public deployment."
