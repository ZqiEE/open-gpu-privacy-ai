from __future__ import annotations

from api.secure_artifact_pack import generate_artifact_key


def main() -> int:
    print(generate_artifact_key())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
