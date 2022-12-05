import csv
import os
from models import Word, database_setup

database_setup()
csv_name = "./words.csv"

if not os.path.exists(csv_name):
    raise FileNotFoundError(f"File {csv_name} not found")

word_set = set()
# for row in csv.reader(csv_name):
with open(csv_name) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=",")
    line_count = 0
    for row in csv_reader:
        words = row[0].split(",")
        for word in words:
            word = word.strip()
            if "Advertisement" not in word:
                word = word.lower()
            word_set.add(word)

for word in word_set:
    words_row = Word.create(word=word)
print(word_set)
