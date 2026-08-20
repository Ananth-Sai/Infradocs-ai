from pathlib import Path
from pypdf import PdfReader


def load_text(filepath: str) -> str:
    """Load raw text from a .pdf, .md, or .txt file."""
    if filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        return Path(filepath).read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Split text into chunks along paragraph boundaries, not raw character
    counts. Groups whole paragraphs together up to chunk_size, carrying a
    bit of the previous chunk forward (overlap) so facts near a boundary
    don't become unretrievable.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current_chunk) + len(p) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + p
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = (current_chunk[-overlap:] + "\n\n" + p) if overlap > 0 else p

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def ingest_folder(folder: str = "docs") -> list[dict]:
    """Returns a list of {text, source, chunk_id} dicts for every chunk
    across every file in the folder."""
    all_chunks = []
    for filepath in Path(folder).glob("*"):
        if filepath.suffix not in [".pdf", ".txt", ".md"]:
            continue
        raw = load_text(str(filepath))
        chunks = chunk_text(raw)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": filepath.name,
                "chunk_id": f"{filepath.stem}_{i}",
            })
    return all_chunks


if __name__ == "__main__":
    chunks = ingest_folder("docs")
    print(f"Total chunks: {len(chunks)}")
    for c in chunks[:3]:
        print("\n---")
        print(f"Source: {c['source']} | ID: {c['chunk_id']}")
        print(c["text"][:300])
