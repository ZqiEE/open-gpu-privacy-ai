from __future__ import annotations

import argparse

from node_client.identity import NodeIdentity


def main() -> None:
    parser = argparse.ArgumentParser(description="Show or create local node identity")
    parser.add_argument("--identity-path", default="runtime_data/node_identity.json")
    args = parser.parse_args()
    identity = NodeIdentity(args.identity_path)
    print(identity.get_or_create())


if __name__ == "__main__":
    main()
