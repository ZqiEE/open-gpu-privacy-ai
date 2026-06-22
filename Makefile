PYTHON ?= python
API_HOST ?= 127.0.0.1
API_PORT ?= 8000

.PHONY: install validate test api node smoke maintain demo-training worker-check clean

install:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) validate.py

test:
	$(PYTHON) -m pytest -q

api:
	uvicorn api.main:app --reload --host $(API_HOST) --port $(API_PORT)

node:
	$(PYTHON) node_client/client.py --api-url http://$(API_HOST):$(API_PORT) --contribution 30

smoke:
	$(PYTHON) scripts/smoke_api.py --api-url http://$(API_HOST):$(API_PORT)

maintain:
	$(PYTHON) scripts/queue_maintenance.py --api-url http://$(API_HOST):$(API_PORT)

demo-training:
	$(PYTHON) scripts/demo_training_flow.py --api-url http://$(API_HOST):$(API_PORT)

worker-check:
	$(PYTHON) scripts/worker_self_check.py

clean:
	rm -rf runtime_data .pytest_cache __pycache__ api/__pycache__ node_client/__pycache__ tests/__pycache__
