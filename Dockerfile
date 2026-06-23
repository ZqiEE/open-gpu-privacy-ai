FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY node_client ./node_client
COPY docs ./docs
COPY validate.py ./validate.py
COPY index.html ./index.html
COPY dashboard.html ./dashboard.html
COPY BRAND.md ./BRAND.md
COPY SECURITY_BOUNDARY.md ./SECURITY_BOUNDARY.md
COPY PRIVATE_CORE.md ./PRIVATE_CORE.md

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
