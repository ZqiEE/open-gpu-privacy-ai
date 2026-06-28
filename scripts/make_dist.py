from __future__ import annotations

import argparse
import shutil
import tarfile
import zipfile
from pathlib import Path


EXCLUDES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "runtime_data",
    "dist",
}


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDES for part in path.parts)


def copy_tree(root: Path, target: Path) -> None:
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if should_skip(rel):
            continue
        dest = target / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)


def make_zip(src: Path, out: Path) -> None:
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in src.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(src.parent))


def make_targz(src: Path, out: Path) -> None:
    with tarfile.open(out, "w:gz") as tf:
        tf.add(src, arcname=src.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Ailovanta install packages")
    parser.add_argument("--version", default="local")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    dist = root / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)

    package_dir = dist / f"ailovanta-{args.version}"
    package_dir.mkdir(parents=True, exist_ok=True)
    copy_tree(root, package_dir)

    (dist / "install_linux.sh").write_text((root / "scripts" / "install_linux.sh").read_text(encoding="utf-8"), encoding="utf-8")
    (dist / "install_windows.ps1").write_text((root / "scripts" / "install_windows.ps1").read_text(encoding="utf-8"), encoding="utf-8")

    make_zip(package_dir, dist / f"ailovanta-{args.version}.zip")
    make_targz(package_dir, dist / f"ailovanta-{args.version}.tar.gz")
    print("Built", dist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
