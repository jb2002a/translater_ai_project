from pre_process import PdfToTextConvert as Convert
from pre_process import PreProcessing as PreProcess


def main():
    """
    Main function to convert PDF to text.
    """
    # Set the page range to convert
    start_page = 20  # Starting page index (0-based)
    end_page = 21  # Ending page index (0-based)
    pdf_path = "D:\\Pdf\\test.pdf"

    print(f"Converting PDF pages {start_page} to {end_page}...")

    text = Convert.pdf_to_text(pdf_path, start_page, end_page)

    print("Start pre-processing the text...")

    # text = PreProcess.pre_process_text(text)

    print("PDF conversion completed! Output saved to output.txt")

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
