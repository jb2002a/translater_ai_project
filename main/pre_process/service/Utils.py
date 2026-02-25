import sqlite3

# 텍스트 파일로 저장하는 함수


def generate_text_file_du(text):
    # Make text file with text_output
    with open("output_du.txt", "w", encoding="utf-8") as f:
        f.write(text)


def generate_text_file_ko(text):
    # Make text file with text_output
    with open("output_ko.txt", "w", encoding="utf-8") as f:
        f.write(text)


# read from db
def read_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT german_sentence FROM processed_sentences")
    sentences = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sentences
