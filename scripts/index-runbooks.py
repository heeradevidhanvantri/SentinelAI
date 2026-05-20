#!/usr/bin/env python3
"""Index sample runbooks and architecture docs into Pinecone."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.rag import RAGService


async def main():
    rag = RAGService()
    samples = Path(__file__).parent.parent / "samples"

    for md_file in (samples / "runbooks").glob("*.md"):
        content = md_file.read_text()
        await rag.index_document(
            doc_id=md_file.stem,
            content=content,
            metadata={"title": md_file.stem, "type": "runbook"},
            namespace="runbooks",
        )
        print(f"Indexed runbook: {md_file.name}")

    for md_file in (samples / "architecture").glob("*.md"):
        content = md_file.read_text()
        await rag.index_document(
            doc_id=md_file.stem,
            content=content,
            metadata={"title": md_file.stem, "type": "architecture"},
            namespace="architecture",
        )
        print(f"Indexed architecture: {md_file.name}")


if __name__ == "__main__":
    asyncio.run(main())
