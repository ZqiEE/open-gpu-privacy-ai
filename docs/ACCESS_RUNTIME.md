# Access Runtime

v2.4 adds access levels, guarded package records, quorum approval, runtime checks, execution windows, grants, fingerprints, and slashing.

```bash
make access-demo
python -m pytest tests/test_model_access_policy.py tests/test_quorum_policy.py tests/test_runtime_check.py tests/test_execution_window.py tests/test_package_guard.py tests/test_slashing_policy.py -q
```
