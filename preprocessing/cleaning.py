
import re
import hunspell

# NOTE: Strictly speaking, the german dictionaries are not needed anymore,
#       but I left this here for future use with different languages
_hunspell_files = {
    "de": ["/usr/share/hunspell/de_DE.dic", "/usr/share/hunspell/de_DE.aff"],
    "en": ["/usr/share/hunspell/en_US.dic", "/usr/share/hunspell/en_US.aff"],
    "es": ["/usr/share/hunspell/es_ES.dic", "/usr/share/hunspell/es_ES.aff"],
    "fr": ["/usr/share/hunspell/fr_FR.dic", "/usr/share/hunspell/fr_FR.aff"],
    "it": ["/usr/share/hunspell/it_IT.dic", "/usr/share/hunspell/it_IT.aff"],
}

# a variable to cache spellcheckers used in this module
_spellchecker_cache = {}


# return the prepared spellchecker for the given language or initialize a
# new one and keep it
def __get_spellchecker(language_code):
    result = _spellchecker_cache.get(language_code, None)
    if not result:
        result = hunspell.HunSpell(*_hunspell_files[language_code])
        _spellchecker_cache[language_code] = result
    return result


def __should_remove_hyphen_between(word1: str, word2: str, language_code):
    """
    Check if a character "-" should be removed from the first word based
    on language characteristics
    :return: False if the hyphen should not be removed,
             Return a str (the combined word) otherwise
    """
    result = False
    combined = word1.rstrip("-") + word2

    if language_code == "de":
        # if the language is german, just check if the second word begins
        # with a small letter
        if isinstance(word2, str) and len(word2) > 0 and word2[0].islower():
            result = combined
    else:
        spell_checker = __get_spellchecker(language_code)
        # when checking the word, remove non-letter characters from both ends
        # this handles cases like "(final-ly)"
        word_to_check = re.compile(r"^\W*").sub("", re.compile(r"\W*$").sub("", combined))
        # if the combined word without the hyphen is recognized we assume
        # that the words should be de-hyphenated
        if spell_checker.spell(word_to_check):
            result = combined
    return result


def lines_remove_hyphens(line1: str, line2: str, language_code: str) -> (str, str):
    result = (line1, line2)
    if re.compile("-$").findall(line1):
        # split the two lines into words
        words1, words2 = map(lambda l: l.split(" "), [line1, line2])
        check_result = __should_remove_hyphen_between(words1[-1], words2[0], language_code)
        if isinstance(check_result, str):
            # pull the combined word into the first line
            words1[-1] = check_result
            words2 = words2[1:]
            result = tuple(map(lambda ws: " ".join(ws), [words1, words2]))
        else:
            print("Not removing hyphen: ", words1[-1], words2[0])
    return result
