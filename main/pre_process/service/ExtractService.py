# This file converts PDFs to text format and saves the text in a .txt file.
# It uses the PyMuPDF library (fitz) to read the PDF and extract text from specified pages.


import fitz

# 추출 함수
def extract_text(doc):
    full_text = ""

    for page in doc:
        full_text += page.get_text("text") + ""

    return full_text


