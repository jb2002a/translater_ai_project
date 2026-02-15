# This file converts PDFs to text format and saves the text in a .txt file.
# It uses the PyMuPDF library (fitz) to read the PDF and extract text from specified pages.


import fitz


def pdf_to_text(pdf_path, start_idx, end_idx):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(start_idx, end_idx + 1):
        page = doc.load_page(page_num)
        text += page.get_text("text")
    return text


def generate_text_file(text):
    # Make text file with text_output
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text)
