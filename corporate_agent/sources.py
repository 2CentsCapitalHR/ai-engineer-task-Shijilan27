import os
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


def _safe_filename(url: str) -> str:
    keep = [c if c.isalnum() else "_" for c in url]
    name = "".join(keep)
    return name[:120]


def _extract_html_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines()]
    return "\n".join([l for l in lines if l])


def _extract_docx_text(content: bytes) -> str:
    try:
        from io import BytesIO
        from docx import Document

        doc = Document(BytesIO(content))
        parts = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text.strip())
        return "\n".join(parts)
    except Exception:
        return ""


def _extract_pdf_text(content: bytes) -> str:
    try:
        from io import BytesIO
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(content))
        pages: List[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception:
        return ""


def fetch_urls(urls: List[str], save_dir: Optional[str] = None) -> List[Dict]:
    """Fetch URLs and extract text content. Returns a list of reference docs.

    Each entry: {"title": str, "text": str, "source": str}
    """
    results: List[Dict] = []
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)

    for url in urls:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            text = ""
            if "text/html" in content_type:
                text = _extract_html_text(resp.content)
            elif "/pdf" in content_type:
                text = _extract_pdf_text(resp.content)
            elif "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type or url.lower().endswith(".docx"):
                text = _extract_docx_text(resp.content)
            else:
                # Try as HTML fallback
                text = _extract_html_text(resp.content)

            title = url
            if save_dir:
                fname = _safe_filename(url)
                with open(os.path.join(save_dir, f"{fname}.txt"), "w", encoding="utf-8") as f:
                    f.write(text)
            results.append({"title": title, "text": text, "source": url})
        except Exception:
            continue

    return results

