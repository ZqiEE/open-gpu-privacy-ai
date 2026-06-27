from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import zipfile
from pathlib import Path
from urllib import request


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_extract_zip(path: Path, dest: Path) -> list[str]:
    files: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            target = (dest / member.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError("unsafe zip path")
            archive.extract(member, dest)
            files.append(str(dest / member.filename))
    return files


def safe_extract_tar(path: Path, dest: Path) -> list[str]:
    files: list[str] = []
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            target = (dest / member.name).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError("unsafe tar path")
        archive.extractall(dest)
        files = [str(dest / member.name) for member in archive.getmembers()]
    return files


def write_cache_index(root: Path, record: dict) -> None:
    index = root / "artifact_cache.json"
    items = []
    if index.exists():
        try:
            items = json.loads(index.read_text(encoding="utf-8"))
        except Exception:
            items = []
    items.append(record)
    index.write_text(json.dumps(items[-200:], ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_artifact(url: str, output_dir: str, expected_sha256: str | None = None, extract: bool = True) -> dict:
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http/https artifact urls are supported")
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = url.rstrip("/").split("/")[-1] or "artifact.bin"
    target = target_dir / filename
    with request.urlopen(url, timeout=120) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    digest = sha256_file(target)
    if expected_sha256 and digest != expected_sha256:
        target.unlink(missing_ok=True)
        raise ValueError("artifact sha256 mismatch")

    extracted_to = None
    extracted_files: list[str] = []
    if extract and target.suffix.lower() == ".zip":
        extracted_to = target_dir / target.stem
        extracted_to.mkdir(parents=True, exist_ok=True)
        extracted_files = safe_extract_zip(target, extracted_to)
    elif extract and (target.name.endswith(".tar.gz") or target.suffix.lower() in {".tgz", ".tar"}):
        extracted_to = target_dir / target.name.replace(".tar.gz", "").replace(".tgz", "").replace(".tar", "")
        extracted_to.mkdir(parents=True, exist_ok=True)
        extracted_files = safe_extract_tar(target, extracted_to)

    record = {"url": url, "path": str(target), "sha256": digest, "bytes": target.stat().st_size, "extracted_to": str(extracted_to) if extracted_to else None, "extracted_files": extracted_files[:200]}
    write_cache_index(target_dir, record)
    return record
