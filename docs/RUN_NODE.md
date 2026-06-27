# Run Node

```bash
uvicorn api.main_code:app --reload
```

```bash
python scripts/run_worker.py --server http://127.0.0.1:8000 --once
```

```bash
python scripts/run_worker.py --server http://127.0.0.1:8000 --contribution-percent 30
```

```bash
python scripts/run_worker.py --server http://127.0.0.1:8000 --enable-gpu --contribution-percent 30
```
