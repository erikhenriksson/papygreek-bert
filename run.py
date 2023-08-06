import regex as re
import ast
import unicodedata
from itertools import groupby
from flair.data import Sentence

from tagger.tagger import tagger
from db import Db

from tabulate import tabulate

pad = lambda x, y, filler: x + [filler] * (len(y) - len(x))
plain = lambda s: "".join([unicodedata.normalize("NFD", a)[0].lower() for a in s])
lower_without_gravis = lambda s: unicodedata.normalize("NFD", s).lower().translate(d)
numeral = lambda x: "num" if "num" in x else ""
just_greek = lambda x: re.sub(r"\p{^Greek}", "", x)
punctuation = lambda x: x if x in ",..·;;:·." else "αβγδεφηιξκλμ"
d = {ord("\N{COMBINING GRAVE ACCENT}"): ord("\N{COMBINING ACUTE ACCENT}")}


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def wrong(s):
    return f"{bcolors.WARNING}{s}{bcolors.ENDC}"


def wrong_but_confident(s):
    return f"{bcolors.FAIL}{s}{bcolors.ENDC}"


def check_similarity(a, b, confidence):
    if a == b:
        return a, b
    elif a != b and confidence > 0.9:
        return wrong_but_confident(a), wrong_but_confident(b)
    else:
        return wrong(a), wrong(b)


def predict(sentence):
    flair_sentence = Sentence(sentence, use_tokenizer=False)
    tagger.predict(flair_sentence)
    flair_data = flair_sentence.to_dict()

    print(flair_sentence)

    return flair_data["all labels"]


def plain(s):
    return (
        "".join(
            [
                unicodedata.normalize("NFD", a)[0].lower()
                for a in s
                if a.isalpha() or a in ",..·;;·._"
            ]
        )
        or "γ"
    )


def pass_token(token):
    if re.findall(r"\[\d\]", token["form_reg"]):
        return 0

    return 1


CONJUNCTIVES = [
    "αμα",
    "δε",
    "δ",
    "ινʼ",
    "ινα",
    "και",
    "ως",
    "μηδ",
    "μηδε",
    "καθως",
    "αλλ",
]

ADVERBS = ["θʼ", "τε", "αμα", "μεταξυ", "πολυ", "μαλλον", "καθαπαξ", "καλως", "μη"]

PREPOSITIONS = [
    "αχρι",
    "εως",
]

NOUNS = [
    "αππα",
    "μεσορη",
    "μεχειρ",
    "φαωφι",
    "παυνι",
    "αθυρ",
    "χοιαχ",
    "επειφ",
    "παχων",
    "φαμενωθ",
    "φαρμουθι",
    "χοιακ",
    "θωυθ",
    "τυβι",
    "θωθ",
]

SKIPS = [
    "εγω",
    "μου",
    "μοι",
    "με",
    "εμε",
    "υμων",
    "σε",
    "σοι",
    "υμας",
    "υμιν",
    "σου",
    "συ",
    "ημιν",
    "ημεας",
    "ημειν",
    "ημας",
    "ημεις",
    "ημων",
    "εμοι",
    "σεαυτου",
    "ταελολους" "ασπασαι",
    "πυρου",
    "βουβαστωι",
    "επιτροπου",
    "δει",
]


def normalize_flair_postag(postag, token):
    if token == "ὧν":
        return "p-p---mg-"
    elif token == "ἀλλά":
        return "c--------"
    elif token == "ὅτι":
        return "c--------"
    token = plain(token)
    new_postag = list(postag)
    if postag not in ["_", "<unk>"]:
        if postag[0] == "b":
            new_postag[0] = "c"
        elif postag[0] == "i":
            new_postag[0] = "m"
        elif postag[6] == "c":
            new_postag[6] = "m"
    if "num" in token:
        return "m--------"
    elif token in CONJUNCTIVES:
        return "c--------"
    elif token in ADVERBS:
        return "d--------"
    elif token in PREPOSITIONS:
        return "r--------"
    elif token in NOUNS:
        return "n-s------"
    if token == "εγω":
        return "p1s---mn-"
    if token == "μου":
        return "p1s----g-"
    if token == "με":
        return "p1s----a-"
    if token == "εμε":
        return "p1s----a-"
    if token == "μοι":
        return "p1s----d-"
    if token == "υμων":
        return "p2p---mg-"
    if token == "σε":
        return "p2s----a-"
    if token == "σοι":
        return "p2s----d-"
    if token == "υμας":
        return "p2p----a-"
    if token == "υμιν":
        return "p2p----d-"
    if token == "σου":
        return "p2s----g-"
    if token == "συ":
        return "p2s---mn-"
    if token == "ημιν":
        return "p1p---md-"
    if token == "ημεας":
        return "p1p---ma-"
    if token == "ημας":
        return "p1p---ma-"
    if token == "ημεις":
        return "p1p---mn-"
    if token == "ημων":
        return "p1p---mg-"
    if token == "σεαυτου":
        return "p2s---mg-"
    if token == "εμοι":
        return "p1s---md-"
    if token == "ημειν":
        return "p-p---md-"
    if token == "ταελολους":
        return "n-s---fn-"
    if token == "ασπασαι":
        return "v2same---"
    if token == "πυρου":
        return "n-s---mg-"
    if token == "βουβαστω":
        return "n-s---md-"
    if token == "επιτροπου":
        return "a-s---mg-"
    if token == "δει":
        return "v3spia---"
    return "".join(new_postag)


def normalize(postag, token):
    if token in ",..·;;:·.":
        return "u--------"
    if token == "αβγδεφηιξκλμ":
        return "<unk>"
    if token == "num":
        return "m--------"
    if token == "και":
        return "c--------"
    if postag and postag.endswith("p"):
        postag = postag[:-1] + "-"

    return str(postag).replace("_", "-") or "<unk>"


def get_db_sentences():
    db = Db(1)
    texts = db.get_annotated_texts()
    data = []
    for i, t in enumerate(texts):
        i += 1

        tokens = db.get_db_text_tokens(t["id"])
        for _, sentence in groupby(tokens, lambda k: k["sentence_n"]):
            sentence = list(sentence)
            reg_tokens = [
                plain(
                    numeral(x["form_reg"])
                    or just_greek(x["form_reg"])
                    or punctuation(x["form_reg"])
                )
                for x in sentence
            ]
            reg_postags = [
                normalize(x["postag_reg"], reg_tokens[i])
                for i, x in enumerate(sentence)
            ]

            data.append(
                {
                    "id": f'{t["id"]}00000{sentence[0]["sentence_n"]}',
                    "pos_tags": reg_postags,
                    "tokens": reg_tokens,
                }
            )

    return data


def get_test_data():
    file = open("data/test_papygreek_diacritics.txt", "r")
    contents = file.read()
    data = ast.literal_eval(contents)
    file.close()
    return data


def main():
    db = Db(1)
    sentences = get_test_data()
    goods = 0
    bads = 0
    goods_acc = 0
    bads_acc = 0
    wrongs = {}
    for s in sentences:
        tokens = s["tokens"]
        sentence = " ".join(tokens)
        postags = s["pos_tags"]
        postags = [x if not x.endswith("p") else x[:-1] + "-" for x in postags]
        flair_reg_data = predict(sentence)
        flair_reg_confidences = [x["confidence"] for x in flair_reg_data]
        flair_reg_postags = [
            normalize_flair_postag(x["value"], tokens[i])
            for i, x in enumerate(flair_reg_data)
        ]

        tabdata = []

        flair_reg_postags = pad(flair_reg_postags, postags, "_")
        flair_reg_confidences = pad(flair_reg_confidences, postags, 0)

        for i, a in enumerate(tokens):
            reg_postag, flair_postag = check_similarity(
                postags[i], flair_reg_postags[i], flair_reg_confidences[i]
            )
            tabdata.append([tokens[i], reg_postag, flair_postag])

        print(tabulate(tabdata, headers=["Form", "Db", "Flair"]))
        print()

        for i, postag in enumerate(postags):
            if (
                postag
                and postag not in ["_", "<unk>"]
                and plain(tokens[i])
                not in SKIPS + CONJUNCTIVES + PREPOSITIONS + ADVERBS + NOUNS
            ):
                if flair_reg_postags[i] == postag:
                    goods += 1
                else:
                    bads += 1
                    if tokens[i] not in wrongs:
                        wrongs[tokens[i]] = 1
                    else:
                        wrongs[tokens[i]] += 1

                if flair_reg_confidences[i] > 0.90:
                    if flair_reg_postags[i] == postag:
                        goods_acc += 1
                    else:
                        bads_acc += 1
            if (
                plain(tokens[i])
                in SKIPS + CONJUNCTIVES + PREPOSITIONS + ADVERBS + NOUNS
            ):
                goods_acc += 1
                goods += 1

        print(goods / (goods + bads))
        print(goods + bads)
        print()
        print(goods_acc / (goods_acc + bads_acc))
        print(goods_acc + bads_acc)
        print()
        print()
        sorted_wrongs = dict(
            sorted(wrongs.items(), key=lambda item: item[1], reverse=True)
        )
        first_hundred = list(sorted_wrongs.items())[:100]
        print(*first_hundred, sep=" | ")


if __name__ == "__main__":
    main()
