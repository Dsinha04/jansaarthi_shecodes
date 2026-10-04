import pytest
import ingest
from fake_embedder import HashEmbedder


def test_sections_are_tracked():
    text = open("tests/test_corpus/dummy_act.txt").read()
    units = ingest.build_units([(None, text)])
    secs = {u[2] for u in units}
    assert "Section 3. Loan application" in secs
    assert "Section 6. Complaint to the Registrar" in secs


def test_long_paragraph_is_split_without_losing_words():
    words = [f"w{i}" for i in range(500)]
    chunks = ingest.chunk_units([(words, 1, "Section 1. X")], size=100, overlap=20)
    assert all(len(c["text"].split()) <= 150 for c in chunks)
    joined = " ".join(c["text"] for c in chunks)
    assert "w0" in joined and "w499" in joined
    assert all(c["section"] == "Section 1. X" and c["page"] == 1 for c in chunks)


def _pdf(path, pages):
    reportlab = pytest.importorskip("reportlab.pdfgen.canvas")
    c = reportlab.Canvas(str(path))
    for lines in pages:
        y = 800
        for ln in lines:
            c.drawString(50, y, ln)
            y -= 18
        c.showPage()
    c.save()


def test_pdf_pages_and_sections(tmp_path):
    pdf = tmp_path / "act.pdf"
    _pdf(pdf, [
        ["Section 10. Alpha rules", "Alpha rules say that members must attend the annual meeting of the society."],
        ["Section 11. Beta rules", "Beta rules say that every loan needs a written sanction letter from the society."],
    ])
    index, meta, warnings = ingest.build_index([pdf], HashEmbedder(), size=30, overlap=5)
    alpha = next(m for m in meta if "Alpha rules say" in m["text"])
    beta = next(m for m in meta if "Beta rules say" in m["text"])
    assert alpha["page"] == 1 and alpha["section"].startswith("Section 10")
    assert beta["page"] == 2 and beta["section"].startswith("Section 11")
    assert not warnings


def test_empty_pdf_gives_warning(tmp_path):
    empty, good = tmp_path / "scan.pdf", tmp_path / "good.txt"
    _pdf(empty, [[]])
    good.write_text("Section 1. Test\nSome real text about loans.")
    _, meta, warnings = ingest.build_index([empty, good], HashEmbedder())
    assert any("scan.pdf" in w and "no text" in w for w in warnings)
    assert all(m["source"] == "good.txt" for m in meta)


def test_all_empty_raises(tmp_path):
    empty = tmp_path / "scan.pdf"
    _pdf(empty, [[]])
    with pytest.raises(ValueError):
        ingest.build_index([empty], HashEmbedder())
