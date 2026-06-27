from __future__ import annotations

import json

from api.migrations import MigrationRunner


def main() -> int:
    print(json.dumps(MigrationRunner().run(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
