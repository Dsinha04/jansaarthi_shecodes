"""Build the FAISS index from files in data/docs (.pdf, .txt, .md).
Chunks remember their page number and the section heading they sit under, so answers can cite them.
Run:  python ingest.py
"""
import json
import re
import faiss
import config

# "Section 84 ...", "Bye-law 12 ...", "Chapter 3 ...", or short numbered headings like "84. Disputes"
HEADING = re.compile(
    r"^\s*(?:(?:section|sec\.?|article|rule|regulation|bye-?law|clause|chapter)\s+\d+[a-z]?\b.{0,80}"
    r"|\d{1,3}[A-Z]?\.\s+[A-Z][^\n]{3,80})\s*$", re.I)


def read_pages(path):
    """Return [(page_number or None, text)]."""
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(str(path)).pages)]
    return [(None, path.read_text(encoding="utf-8", errors="ignore"))]


def build_units(pages):
    """Split pages into paragraphs, each tagged with (page, section heading in force at its start)."""
    units, section = [], None

    def flush(buf, page, sec):
        if buf:
            units.append((" ".join(buf).split(), page, sec))

    for page, text in pages:
        buf, buf_sec = [], section
        for line in text.splitlines():
            s = line.strip()
            if not s:
                flush(buf, page, buf_sec)
                buf = []
                continue
            if HEADING.match(s):
                flush(buf, page, buf_sec)
                buf = []
                section = s[:90]
            if not buf:
                buf_sec = section
            buf.append(s)
        flush(buf, page, buf_sec)
    return units


def chunk_units(units, size=config.CHUNK_WORDS, overlap=config.CHUNK_OVERLAP):
    chunks, cur, meta, last_page = [], [], None, None

    def emit():
        chunks.append({"text": " ".join(cur), "page": meta[0], "page_end": last_page, "section": meta[1]})

    for words, page, sec in units:
        pieces = [words[i:i + size] for i in range(0, len(words), size)] if len(words) > size * 1.5 else [words]
        for w in pieces:
            if cur and len(cur) + len(w) > size:
                emit()
                cur = cur[-overlap:]
                meta = (page, sec)
            if not cur:
                meta = (page, sec)
            cur = cur + w
            last_page = page
    if cur:
        emit()
    return chunks


def build_index(files, embedder, size=config.CHUNK_WORDS, overlap=config.CHUNK_OVERLAP):
    meta, warnings = [], []
    for f in files:
        chunks = chunk_units(build_units(read_pages(f)), size, overlap)
        if not chunks:
            warnings.append(f"{f.name}: no text extracted (scanned PDF? run OCR first)")
            continue
        joined = " ".join(c["text"] for c in chunks)
        if "\ufffd" in joined or "(cid:" in joined:
            warnings.append(f"{f.name}: text looks garbled (check Hindi / legacy-font PDFs)")
        for i, c in enumerate(chunks):
            meta.append({"source": f.name, "chunk": i, **c})
    if not meta:
        raise ValueError("No text could be extracted from any document")
    emb = embedder.encode_passages([m["text"] for m in meta])
    index = faiss.IndexFlatIP(emb.shape[1])       # exact search is fast enough at this scale
    index.add(emb)
    return index, meta, warnings


def main():
    from embedding import E5Embedder
    files = sorted(p for p in config.DOCS_DIR.rglob("*") if p.suffix.lower() in {".pdf", ".txt", ".md"}
                   and p.name.lower() != "readme.txt")
    if not files:
        raise SystemExit(f"No documents found in {config.DOCS_DIR}")
    index, meta, warnings = build_index(files, E5Embedder())
    for w in warnings:
        print("WARNING:", w)
    config.INDEX_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(config.FAISS_PATH))
    config.META_PATH.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"{len(files)} files -> {len(meta)} chunks. Index saved to {config.INDEX_DIR}")


if __name__ == "__main__":
    main()
