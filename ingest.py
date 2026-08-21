import csv
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard PDF parser
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Optional Word parser
try:
    from docx import Document
except ImportError:
    Document = None

# Optional HTML parser
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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
    """Load and normalize raw text from various document formats (.pdf, .docx, .csv, .json, .html, .md, .txt)."""
    path = Path(filepath)
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf" and PdfReader is not None:
            reader = PdfReader(filepath)
            extracted_pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text.strip())
            return "\n\n".join(extracted_pages)

        elif suffix == ".docx" and Document is not None:
            doc = Document(filepath)
            return "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

        elif suffix == ".csv":
            rows = []
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                for row in reader:
                    cleaned_row = [col.strip() for col in row if col.strip()]
                    if cleaned_row:
                        rows.append(", ".join(cleaned_row))
            return "\n".join(rows)

        elif suffix == ".json":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            if isinstance(data, list):
                return "\n\n".join(json.dumps(item, indent=2) for item in data)
            return json.dumps(data, indent=2)

        elif suffix in [".html", ".htm"] and BeautifulSoup is not None:
            html_content = path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html_content, "html.parser")
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            return soup.get_text(separator="\n\n").strip()

    except Exception as e:
        logger.warning(f"Specialized parser failed for {filepath} ({e}); falling back to plain text read.")

    # Universal fallback for plain text, markdown, or failed parser fallbacks
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception as e:
        logger.error(f"Failed to read file {filepath}: {e}")
        return ""


def _split_long_text(text: str, max_len: int = 800, overlap: int = 150) -> list[str]:
    """Helper to split arbitrarily long text chunks into overlapping windows."""
    if len(text) <= max_len:
        return [text]
    
    slices = []
    start = 0
    step = max(1, max_len - overlap)
    while start < len(text):
        end = start + max_len
        slices.append(text[start:end])
        if end >= len(text):
            break
        start += step
    return slices


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Split text into semantic chunks along paragraph boundaries.
    
    Groups whole paragraphs up to chunk_size with overlap. If a single paragraph
    exceeds chunk_size, it is safely sub-divided to ensure consistent token lengths.
    """
    if not text or not text.strip():
        return []

    # First split on paragraph breaks
    raw_paragraphs = text.split("\n\n")
    paragraphs: list[str] = []
    
    for p in raw_paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        if len(p_clean) > chunk_size:
            # Sub-split oversized single paragraphs
            paragraphs.extend(_split_long_text(p_clean, max_len=chunk_size, overlap=overlap))
        else:
            paragraphs.append(p_clean)

    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if not current_chunk:
            current_chunk = p
        elif len(current_chunk) + len(p) + 2 <= chunk_size:
            current_chunk += "\n\n" + p
        else:
            chunks.append(current_chunk)
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + "\n\n" + p
            else:
                current_chunk = p

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def ingest_folder(folder: str = "docs") -> list[dict]:
    """Returns a list of {text, source, chunk_id} dicts for every chunk
    across all supported files in the folder."""
    all_chunks = []
    target_dir = Path(folder)
    
    if not target_dir.exists():
        logger.warning(f"Target folder '{folder}' does not exist.")
        return all_chunks

    for filepath in sorted(target_dir.glob("*")):
        # Skip subdirectories or hidden files
        if not filepath.is_file() or filepath.name.startswith("."):
            continue
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        raw = load_text(str(filepath))
        if not raw:
            continue

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
