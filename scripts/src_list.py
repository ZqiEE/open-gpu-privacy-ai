from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT = Path("runtime_data/github_code_sources.json")


def load(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": "ailovanta.github_code_sources.v1", "sources": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert(data: dict, name: str, url: str, branch: str, policy: str, hint: str, enabled: bool) -> dict:
    items = data.setdefault("sources", [])
    rec = next((x for x in items if x.get("name") == name or x.get("url") == url), None)
    new = {"name": name, "url": url, "branch": branch, "license_policy": policy, "license_hint": hint, "enabled": enabled}
    if rec:
        rec.update(new)
        return rec
    items.append(new)
    return new


def main() -> int:
    p = argparse.ArgumentParser(description="Manage code source list")
    p.add_argument("--file", default=str(DEFAULT))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--url", required=True)
    a.add_argument("--branch", default="main")
    a.add_argument("--policy", default="permissive_only")
    a.add_argument("--license-hint", default="unknown")
    a.add_argument("--disabled", action="store_true")
    sub.add_parser("list")
    d = sub.add_parser("disable")
    d.add_argument("--name", required=True)
    e = sub.add_parser("enable")
    e.add_argument("--name", required=True)
    args = p.parse_args()
    path = Path(args.file)
    data = load(path)
    if args.cmd == "add":
        rec = upsert(data, args.name, args.url, args.branch, args.policy, args.license_hint, not args.disabled)
        save(path, data)
        print(json.dumps({"ok": True, "source": rec}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd in {"disable", "enable"}:
        ok = False
        for item in data.get("sources", []):
            if item.get("name") == args.name:
                item["enabled"] = args.cmd == "enable"
                ok = True
        save(path, data)
        print(json.dumps({"ok": ok, "sources": data.get("sources", [])}, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
