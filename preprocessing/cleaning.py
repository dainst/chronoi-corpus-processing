
import re
import hunspell

logging = True

# NOTE: Strictly speaking, the german dictionaries are not needed anymore,
#       but I left this here for future use with different languages
hunspell_files = {
    "en": ["/usr/share/hunspell/en_US.dic", "/usr/share/hunspell/en_US.aff"],
    "de": ["/usr/share/hunspell/de_DE.dic", "/usr/share/hunspell/de_DE.aff"]
}


def log_replacement(before, after):
    if logging:
        print("-------> Replacing:")
        print(" before: '%s'" % before)
        print("  after: '%s'" % after)


def __replace_regex_group_by_whitespace(match, group_no):
    replacement = " " * len(match.group(group_no))
    start = match.string[0:match.start(group_no)]
    end = match.string[match.end(group_no):]
    return start + replacement + end


# a paragraph heading is displayed to the left of the text: 2 or more whitespaces
# followed by the heading (first group), then two or more whitespaces again
regex_text_surrounded_by_whitespace_left = re.compile(r"^\s{2,}(([^\s]+ )+)\s{2,}")
regex_text_preceded_by_whitespace_right = re.compile(r"\s{4,}(([^\s]* ?)+)")


# remove the first line from a page
def page_remove_first_line(page_text):
    lines = page_text.splitlines()
    return "\n".join(lines[1:])


def __line_delete_text_surrounded_by_whitespace(line, regex, expected_max_length_ratio):
    result = line
    match = regex.search(line)

    if match:
        # make sure that the supposed heading is not longer than expected
        part_of_line_ratio = (match.end() - match.start()) / float(len(line))
        if part_of_line_ratio < expected_max_length_ratio:
            # replace the matched group with as many whitespace as chars
            result = __replace_regex_group_by_whitespace(match, 1)
            log_replacement(line, result)
    return result


# Delete a paragraph heading that is left of the main text
# optionally define a maximum length of the replacement as a ratio
# of the whole line. The default assumes that the actual text starts
# at least after half the text
def line_delete_text_surrounded_by_whitespace_left(line, expected_max_length_ratio=0.5):
    return __line_delete_text_surrounded_by_whitespace(
        line,
        regex_text_surrounded_by_whitespace_left,
        expected_max_length_ratio)


# Delete a paragraph heading that is right of the main text
# optionally define a maximum length of the replacement as a ratio
# of the whole line. The default assumes that the actual text starts
# at least after half the text
def line_delete_text_surrounded_by_whitespace_right(line, expected_max_length_ratio=0.5):
    return __line_delete_text_surrounded_by_whitespace(
        line,
        regex_text_preceded_by_whitespace_right,
        expected_max_length_ratio)


def line_delete_if_whitespace_exceeds(line, min_whitespace_ratio=0.7):
    """
    Return the empty string if the amount of whitespace characters relative to len(line)
    is bigger then the min_whitespace_ratio (defaults to 70 percent.) Return the input
    line otherwise.
    """
    result = line
    if len(line) != 0:
        num_whitespace_chars = len(re.compile(r"\s").findall(line))
        whitespace_ratio = num_whitespace_chars / float(len(line))
        if whitespace_ratio > min_whitespace_ratio:
            result = ""
            log_replacement(line, result)
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
        # prepare the spell checker with the appropriate language files
        dictionaries = hunspell_files[language_code]
        spell_checker = hunspell.HunSpell(dictionaries[0], dictionaries[1])
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
            print("TRUE: ", words1[-1], words2[0], check_result)
            # pull the combined word into the first line
            words1[-1] = check_result
            words2 = words2[1:]
            result = tuple(" ".join(words) for words in [words1, words2])
        else:
            print("FALSE: ", words1[-1], words2[0], check_result)
    return result
