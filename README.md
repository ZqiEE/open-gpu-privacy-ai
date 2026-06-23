# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

## v2.4 Guarded Runtime Pack

Added:

- `api/model_access_policy.py`
- `api/protected_model_package.py`
- `api/quorum_policy.py`
- `api/guardian_registry.py`
- `api/runtime_check.py`
- `api/execution_window.py`
- `api/execution_grant_store.py`
- `api/model_fingerprint.py`
- `api/slashing_policy.py`
- `scripts/access_policy_demo.py`
- `docs/ACCESS_RUNTIME.md`
- guarded runtime tests

## v2.3 Distributed Model Registry Pack

Added:

- `api/model_package.py`
- `api/distributed_model_registry.py`
- `api/model_node_inventory.py`
- `api/model_router.py`
- `scripts/seed_distributed_model_demo.py`
- `scripts/model_report.py`

## Run

```bash
python scripts/access_policy_demo.py
python -m pytest tests/test_model_access_policy.py tests/test_quorum_policy.py tests/test_runtime_check.py tests/test_execution_window.py tests/test_package_guard.py tests/test_slashing_policy.py -q
```
