# This file converts PDFs to text format and saves the text in a .txt file.
# It uses the PyMuPDF library (fitz) to read the PDF and extract text from specified pages.

import re
import fitz


def _normalize_line_breaks(text: str) -> str:
    """줄바꿈을 공백으로 바꿔 이후 청킹/전처리가 올바르게 되도록 함."""
    text = re.sub(r"[\r\n]+", " ", text)
    return re.sub(r" +", " ", text).strip()


# 추출 함수
def extract_text(doc_path):
    full_text = ""
    doc = fitz.open(doc_path)

    for page in doc:
        full_text += page.get_text("text") + ""

    return _normalize_line_breaks(full_text)
