# Ailovanta Public Launch Checklist

Use this before sharing the repository publicly, posting on social media, or sending it to developers, investors, or early users.

## Repository

- [ ] Public repository name is `ailovanta`.
- [ ] README explains what Ailovanta is in the first screen.
- [ ] README includes local run steps.
- [ ] README links to Ailovanta Core without exposing private implementation details.
- [ ] `BRAND.md` is consistent with README.
- [ ] `docs/PROJECT_STATUS.md` clearly separates done and not done.
- [ ] Issue templates exist.
- [ ] Pull request template exists.

## Safety boundary

- [ ] No credentials are committed.
- [ ] No `.env` files are committed.
- [ ] No model weights are committed.
- [ ] No private datasets are committed.
- [ ] No runtime databases are committed.
- [ ] No user logs are committed.
- [ ] Public repository does not contain Ailovanta Core internals.

## Local checks

```bash
python validate.py
python -m pytest -q
```

## Runtime check

```bash
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/app
http://127.0.0.1:8000/dashboard
http://127.0.0.1:8000/docs
```

Then run:

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```

## Public claim

Use:

```text
Ailovanta is building a distributed AI compute network. The current release is a local MVP with node registration, job dispatch, verification, training job records, and a public/private architecture boundary.
```

Avoid:

```text
Ailovanta has already solved global distributed AI training.
```
