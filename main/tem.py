# read the philosophy_translation.db and save the german_sentence column to a text file.
# This file is used to read the sentences from the database and save them to a text file

from .pre_process.service.Utils import read_from_db, generate_text_file_du

if __name__ == "__main__":
    # Read sentences from the database and save to text file
    sentences = read_from_db("philosophy_translation.db")
    generate_text_file_du("\n".join(sentences))
