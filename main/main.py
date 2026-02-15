import os
from dotenv import load_dotenv
from pre_process import PdfToTextConvert as Convert
from pre_process import PreProcessing as PreProcess
import post_process.Initial_translate as InitialTranslate

# Load environment variables from .env file
load_dotenv()


def main():
    """
    Main function to convert a single PDF page to text and translate.
    """
    # 단일 페이지 인덱스 지정
    idx = 20  # 번역할 페이지 인덱스 (0-based)
    pdf_path = "D:\\Pdf\\test.pdf"

    print(f"Gathering text data from PDF page {idx}...")

    text = Convert.pdf_to_text(pdf_path, idx)

    print("Start pre-processing the text...")
    text = PreProcess.pre_process_text(text)

    print("PDF conversion completed! Output saved to output_du.txt")
    Convert.generate_text_file_du(text)

    author = "Wilhelm Dilthey"
    book_title = "Einleitung in die Geisteswissenschaften"

    print("Start initial translation from German to Korean...")
    translated_text = InitialTranslate.initial_translate(text, author, book_title)

    print("Initial translation completed! Output saved to output_ko.txt")
    Convert.generate_text_file_ko(translated_text)


if __name__ == "__main__":
    main()
