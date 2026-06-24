from __future__ import annotations

import argparse
import json

from api.foundation_result_import import import_foundation_result_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Import ailovanta-core foundation result into public runtime")
    parser.add_argument("path")
    args = parser.parse_args()
    result = import_foundation_result_file(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
