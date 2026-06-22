from __future__ import annotations

import tempfile
from pathlib import Path

from node_client.identity import NodeIdentity


def test_local_node_identity_is_stable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        identity = NodeIdentity(Path(tmp) / "identity.json")
        first = identity.get_or_create()
        second = identity.get_or_create()
        assert first == second
        assert first.startswith("node_")
