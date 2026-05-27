import re
from pathlib import Path

import pdfplumber
import fitz  # PyMuPDF


_WS_RE = re.compile(r"\s+")
_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _extract_page_columnar(page) -> str:
    """Extract a page's text in column-aware reading order.

    PyMuPDF's default sort=True flattens by y-coordinate, which interleaves
    columns on two-column papers. Instead, group text blocks by column
    (using the page midline) and read top-to-bottom within each column.
    """
    blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, type)
    if not blocks:
        return ""
    page_width = page.rect.width
    midline = page_width / 2

    text_blocks = [b for b in blocks if len(b) >= 5 and isinstance(b[4], str) and b[4].strip()]
    if not text_blocks:
        return ""

    left_cx = [(b[0] + b[2]) / 2 for b in text_blocks]
    spread = (max(left_cx) - min(left_cx)) if left_cx else 0
    use_columns = spread > page_width * 0.35

    if not use_columns:
        text_blocks.sort(key=lambda b: (b[1], b[0]))
        return "\n".join(b[4].strip() for b in text_blocks)

    left_col = [b for b in text_blocks if (b[0] + b[2]) / 2 < midline]
    right_col = [b for b in text_blocks if (b[0] + b[2]) / 2 >= midline]
    left_col.sort(key=lambda b: b[1])
    right_col.sort(key=lambda b: b[1])
    ordered = left_col + right_col
    return "\n".join(b[4].strip() for b in ordered)


def extract_text(pdf_path: Path) -> str:
    """Extract full text from a PDF using column-aware ordering.

    Uses PyMuPDF blocks grouped by column to avoid the column-interleaving
    that plagues naive y-sorted extraction on two-column academic papers.
    Falls back to pdfplumber on error.
    """
    try:
        doc = fitz.open(str(pdf_path))
        parts: list[str] = []
        for page in doc:
            parts.append(_extract_page_columnar(page))
        doc.close()
        text = "\n\n".join(parts)
        if text.strip():
            return text
    except Exception:
        pass

    parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n\n".join(parts)


def extract_metadata(pdf_path: Path) -> dict:
    with pdfplumber.open(str(pdf_path)) as pdf:
        md = pdf.metadata or {}
    return {
        "title": md.get("Title") or pdf_path.stem,
        "author": md.get("Author") or "",
        "subject": md.get("Subject") or "",
        "filename": pdf_path.name,
    }


def _normalize_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip().lower()


def _fingerprint(text: str) -> str:
    return _ALNUM_RE.sub("", text.lower())


def verify_citation(quote: str, full_text: str) -> bool:
    """Verify a quote appears in the source text.

    Tries three strategies, increasingly forgiving:
    1. Whitespace-normalized substring match.
    2. Alphanumeric-only fingerprint match (drops punctuation/quotes/dashes).
    3. Sliding-window check on a 40-char prefix + 40-char suffix of the quote,
       which catches cases where the LLM lightly paraphrased the middle but
       quoted the boundaries verbatim.
    """
    if not quote or not quote.strip():
        return False
    n_quote = _normalize_ws(quote)
    n_text = _normalize_ws(full_text)
    if len(n_quote) < 8:
        return False
    if n_quote in n_text:
        return True

    fp_quote = _fingerprint(quote)
    fp_text = _fingerprint(full_text)
    if len(fp_quote) >= 30 and fp_quote in fp_text:
        return True

    if len(fp_quote) >= 80:
        head = fp_quote[:40]
        tail = fp_quote[-40:]
        if head in fp_text and tail in fp_text:
            return True

    # Last-resort: any 60-char contiguous fingerprint window from the quote
    # appearing in the source text counts as verified. Catches LLM cases
    # that preserve a long verbatim run but tweak one or two words.
    window = 60
    if len(fp_quote) >= window:
        for i in range(0, len(fp_quote) - window + 1, 10):
            if fp_quote[i : i + window] in fp_text:
                return True

    return False


def export_pdf(md_path: Path, pdf_path: Path) -> Path:
    import markdown as md_lib
    from weasyprint import HTML, CSS

    md_text = md_path.read_text(encoding="utf-8")
    html_body = md_lib.markdown(
        md_text,
        extensions=["extra", "tables", "fenced_code", "toc"],
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{md_path.stem}</title></head>
<body>{html_body}</body></html>"""

    css = CSS(
        string="""
        @page { size: A4; margin: 2cm; }
        body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }
        h1, h2, h3 { color: #222; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
        """
    )
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(pdf_path), stylesheets=[css])
    return pdf_path
