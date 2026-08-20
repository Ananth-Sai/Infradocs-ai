import csv
import json
from pathlib import Path
from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".md",
    ".txt",
    ".docx",
    ".csv",
    ".json",
    ".html",
    ".htm",
    ".log",
    ".rst",
}


def load_text(filepath: str) -> str:
    """Load raw text from various document formats (.pdf, .docx, .csv, .json, .html, .md, .txt)."""
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(filepath)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    elif suffix == ".docx":
        doc = Document(filepath)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif suffix == ".csv":
        rows = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                if any(row):
                    rows.append(", ".join(row))
        return "\n".join(rows)

    elif suffix == ".json":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        if isinstance(data, list):
            return "\n\n".join(json.dumps(item, indent=2) for item in data)
        return json.dumps(data, indent=2)

    elif suffix in [".html", ".htm"]:
        html_content = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html_content, "html.parser")
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text(separator="\n\n")

    else:
        return path.read_text(encoding="utf-8", errors="ignore")


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
    across all supported files in the folder."""
    all_chunks = []
    for filepath in Path(folder).glob("*"):
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
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
