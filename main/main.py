from dotenv import load_dotenv
import fitz

# Load environment variables from .env file
load_dotenv()


def main():
    doc = fitz.open("D:\\Pdf\\test.pdf")
    full_text = ""

    for page in doc:
        full_text += page.get_text("text") + ""

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(full_text)


if __name__ == "__main__":
    main()
