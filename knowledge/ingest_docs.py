"""Ingest docs into Chroma."""
from __future__ import annotations

import logging
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import json

from config.settings import get_settings
from knowledge.vector_store import get_vector_store
from knowledge.retriever import embed_texts

logger = logging.getLogger(__name__)

def _read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
                text += "\n"
            return text
        except Exception as e:
            logger.warning(f"Failed to read PDF {path}: {e}")
            return ""
    else:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            return ""


def _split_chunks(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """Split into ~500 token chunks, using words as approx tokens."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def _extract_sections(text: str) -> List[Dict[str, str]]:
    """Heuristic: extract sections based on markdown headings."""
    # Split by headings like # or ## or numbered
    lines = text.splitlines()
    sections = []
    current_heading = "Introduction"
    current_content_lines = []
    heading_pattern = re.compile(r"^(#{1,6}\s+|\d+(\.\d+)*\s+|[A-Z][A-Z\s]{3,}:?)")
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            # save previous
            if current_content_lines:
                sections.append({"heading": current_heading, "content": "\n".join(current_content_lines)})
            current_heading = line.lstrip("#").strip()
            current_content_lines = []
        else:
            current_content_lines.append(line)
    if current_content_lines:
        sections.append({"heading": current_heading, "content": "\n".join(current_content_lines)})
    if not sections:
        sections.append({"heading": "General", "content": text})
    return sections


def _infer_machine_tags(filename: str, content: str) -> List[str]:
    tags = []
    lower = (filename + " " + content[:2000]).lower()
    if "turbo" in lower or "engine" in lower or "compressor" in lower or "turbine" in lower:
        tags.append("turbofan")
    if "secom" in lower or "semiconductor" in lower or "chamber" in lower or "wafer" in lower:
        tags.append("secom")
    if "bosch" in lower or "assembly" in lower or "torque" in lower or "station" in lower:
        tags.append("bosch")
    if "vibration" in lower or "lubrication" in lower or "safety" in lower or "lockout" in lower:
        tags.append("all")
    if not tags:
        tags.append("all")
    return tags


def ingest_manuals(manuals_dir: str = "./data/manuals", reset: bool = False) -> int:
    """Load .md/.txt/.pdf from manuals_dir, split, embed, upsert.

    Idempotent: re-running does not duplicate because we use deterministic chunk ids based on hash.
    """
    settings = get_settings()
    store = get_vector_store()
    if reset:
        store.reset()

    manuals_path = Path(manuals_dir)
    if not manuals_path.exists():
        logger.warning(f"Manuals dir {manuals_dir} does not exist")
        return 0

    files = list(manuals_path.glob("*.md")) + list(manuals_path.glob("*.txt")) + list(manuals_path.glob("*.pdf"))
    # also include failure_logs.jsonl as docs
    failure_logs_path = manuals_path / "failure_logs.jsonl"
    extra_files = []
    if failure_logs_path.exists():
        extra_files.append(failure_logs_path)

    all_files = files + extra_files
    logger.info(f"Found {len(all_files)} files to ingest in {manuals_dir}")

    # Prepare batch
    all_ids: List[str] = []
    all_docs: List[str] = []
    all_metas: List[Dict[str, Any]] = []

    count = 0
    for fp in all_files:
        text = _read_file(fp)
        if not text.strip():
            continue

        doc_type = "failure_log" if fp.name == "failure_logs.jsonl" else "manual"
        # Special handling for jsonl failure logs
        if fp.name == "failure_logs.jsonl":
            # Each line is a failure log
            try:
                lines = text.strip().splitlines()
                for line_idx, line in enumerate(lines):
                    try:
                        obj = json.loads(line)
                        # Create document text from fields
                        doc_text = f"Incident {obj.get('incident_id')} Machine {obj.get('machine_type')} Symptoms: {obj.get('symptoms')} Root cause: {obj.get('root_cause')} Fix: {obj.get('fix')} Downtime {obj.get('downtime_minutes')} minutes"
                        chunk_id = hashlib.sha256(f"{fp.name}_{line_idx}_{doc_text[:100]}".encode()).hexdigest()[:16]
                        tags = [obj.get("machine_type", "all")]
                        meta = {
                            "source": fp.name,
                            "section": f"Incident {obj.get('incident_id')}",
                            "page": None,
                            "machine_type_tags": tags,
                            "doc_type": doc_type,
                            "chunk_id": chunk_id,
                        }
                        all_ids.append(chunk_id)
                        all_docs.append(doc_text)
                        all_metas.append(meta)
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to parse failure log line {line_idx}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Failure logs parsing error: {e}")

        sections = _extract_sections(text)
        for sec in sections:
            heading = sec["heading"]
            content = sec["content"]
            chunks = _split_chunks(content, chunk_size=500, overlap=80)
            tags = _infer_machine_tags(fp.name, content)
            for chunk_idx, chunk in enumerate(chunks):
                # deterministic id
                hash_input = f"{fp.name}_{heading}_{chunk_idx}_{chunk[:50]}"
                chunk_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
                meta = {
                    "source": fp.name,
                    "section": heading,
                    "page": None,
                    "machine_type_tags": tags,
                    "doc_type": doc_type,
                    "chunk_id": chunk_id,
                }
                all_ids.append(chunk_id)
                all_docs.append(chunk)
                all_metas.append(meta)
                count += 1

    if not all_docs:
        logger.info("No documents to ingest")
        return 0

    # Embed and upsert in batches
    batch_size = 50
    total_upserted = 0
    for i in range(0, len(all_docs), batch_size):
        batch_ids = all_ids[i : i + batch_size]
        batch_docs = all_docs[i : i + batch_size]
        batch_metas = all_metas[i : i + batch_size]
        embeddings = embed_texts(batch_docs)
        store.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas, embeddings=embeddings)
        total_upserted += len(batch_docs)
        logger.info(f"Upserted batch {i//batch_size+1}: {len(batch_docs)} docs")

    logger.info(f"Ingestion complete: {total_upserted} chunks, store count now {store.count()}")
    return total_upserted


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="./data/manuals")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    ingest_manuals(args.dir, reset=args.reset)


if __name__ == "__main__":
    main()
