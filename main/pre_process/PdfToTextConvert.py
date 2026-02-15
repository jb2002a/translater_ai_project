# This file converts PDFs to text format and saves the text in a .txt file.
# It uses the PyMuPDF library (fitz) to read the PDF and extract text from specified pages.


import fitz


def pdf_to_text(pdf_path, idx):
    doc = fitz.open(pdf_path)
    text = ""

    page = doc.load_page(idx)
    text += page.get_text("text")

    return text


def generate_text_file_du(text):
    # Make text file with text_output
    with open("output_du.txt", "w", encoding="utf-8") as f:
        f.write(text)


def generate_text_file_ko(text):
    # Make text file with text_output
    with open("output_ko.txt", "w", encoding="utf-8") as f:
        f.write(text)
