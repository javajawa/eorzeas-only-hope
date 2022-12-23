from typing import Dict, Tuple

import itertools
import json
import os
import pathlib

from prosegen.prosegen import *


path: pathlib.Path[str] = pathlib.Path("caches")

if not path.is_dir():
    raise FileNotFoundError(path)

data: Dict[str, Tuple[int, int]] = {}

for file in os.listdir(path):
    with (path / file).open("r") as infile:
        _json = json.load(infile)

        for line in _json["quest"]["dialogue"]:
            text = (
                line["text"]
                .replace("─", " - ")
                .replace('<span class="highlight">Forename</span>', "generatedname")
                .replace("</span>", "")
                .replace("<br>", "")
            )
            text = re.sub(r"<span class=\"[^\"]+\">", "", text)

            text = ELLIPSIS_P.sub(r" … \1 ", text)
            text = ELLIPSIS.sub(r" … ", text)
            text = PUNCT.sub(r" \1 ", text)
            text = NDASH.sub(r"\1 –", text)
            text = DQUOTE1.sub(r' "!PUNCT \1 " ', text)
            text = DQUOTE2.sub(r' "!PUNCT \1 " ', text)
            text = SQUOTE1.sub(r' "!PUNCT \1 " ', text)
            text = SQUOTE2.sub(r' "!PUNCT \1 " ', text)
            text = SPACE.sub(" ", text)
            words = text.strip().split(" ")
            
            for word in words:
                word_lower = word.lower()
                if word_lower not in data:
                    data.setdefault(word_lower, (0, 0))

                if word_lower == word:
                    data[word_lower] = (data[word_lower][0], data[word_lower][1] + 1)
                else:
                    data[word_lower] = (data[word_lower][0] + 1, data[word_lower][1])

# words = {word: upper for word, (upper, lower) in data.items() if lower == 0}
words = dict(sorted(data.items(), key=lambda item: item[1][0] + item[1][1], reverse=True))
for word, (upper, lower) in list(itertools.islice(words.items(), 500)):
    print(f"{word:30s} {upper:05d} {lower:05d}")
