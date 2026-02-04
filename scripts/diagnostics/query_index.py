from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from llama_index.core import StorageContext, load_index_from_storage
from app.rag_utils import configure_llamaindex_defaults


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Consulta a probar")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    persist_dir = ROOT / "index_store"

    configure_llamaindex_defaults()
    storage = StorageContext.from_defaults(persist_dir=str(persist_dir))
    index = load_index_from_storage(storage)
    retriever = index.as_retriever(similarity_top_k=args.top_k)

    results = retriever.retrieve(args.query)
    print(f"Query: {args.query}")
    print(f"Top K: {args.top_k}")
    print(f"Results: {len(results)}\n")

    for i, r in enumerate(results, start=1):
        model = r.metadata.get("model") if hasattr(r, "metadata") else None
        score = getattr(r, "score", None)
        text = getattr(r, "text", "")
        snippet = text[:200].replace("\n", " ")
        print(f"#{i} score={score} model={model}")
        print(f"  {snippet}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
