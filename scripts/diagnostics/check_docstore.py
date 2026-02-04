from __future__ import annotations

import json
from pathlib import Path

def main() -> int:
    root = Path(__file__).resolve().parents[2]
    docstore_path = root / "index_store" / "docstore.json"

    print(f"Project root: {root}")
    print(f"Docstore path: {docstore_path}")
    print(f"Docstore exists: {docstore_path.exists()}")

    if not docstore_path.exists():
        return 1

    try:
        data = json.loads(docstore_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Docstore JSON error: {exc}")
        return 2

    count = len(data.get("docstore/data", {}))
    print(f"Docstore document count: {count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
