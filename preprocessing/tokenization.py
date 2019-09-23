
from nltk.data import load

# We use one set of abbreviations for english and german text as they share some of them
# and a falsely concatenated sentence is not too bad for us.
abbreviations = [
    # from german texts
    "s", "jh", "jhs", "ca", "abb", "vs", "a", "o", "n", "z", "p", "x", "c", \
    "jahresh", "beibl", "s.o", "s.d", "tab", "reg", "real-encyclop", "zeitschr", \
    "griech", "brit", "mus", "cat", "corr", "bull", "hell", "mitt", "cos", "mitt", \
    "anc", "berl", "sitzungsber", "epigr", "diz", "chr", "add", "art", "ivn", "nob", \
    # from english texts
    "i.e", "tac", "ann", "suet", "al", "ed", "nos", "no", "ch", "chs", "cf", \
    "e.g", "sp", "spp", "suppl", "etal", "cm", "fig", "figs", "vol"
]

# to not split sentences on "19. Jahrhundert" etc.
number_strings = list(map(str, range(1, 999)))

# to not split sentences on "see p. 19f. or p. 20f."
page_number_f_strings = list(map(lambda i: str(i) + "f", range(1, 9999)))

def sentence_tokenizer(language='english'):
    # load the punkt tokenizer directly, so that we can add some abbreviations
    # cf. https://github.com/nltk/nltk/blob/develop/nltk/tokenize/__init__.py#L105
    tokenizer = load(f"tokenizers/punkt/{language}.pickle")

    # add some abbreviations to those that were learned with the model
    tokenizer._params.abbrev_types.update(abbreviations)
    tokenizer._params.abbrev_types.update(number_strings)
    tokenizer._params.abbrev_types.update(page_number_f_strings)

    return tokenizer
