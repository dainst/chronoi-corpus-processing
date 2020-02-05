
import bs4
import re
import unittest

from pattern_extract import extract, integrate, PositionedText

text_in = "abc_pattern1_defg(hij_pattern2_klmn)"

text_without_simple_pattern = "abcdefg(hijklmn)"

text_without_paren_pattern = "abc_pattern1_defg"

text_without_simple_and_paren_pattern = "abcdefg"

pattern_simple = "_pattern[0-9]_"

pattern_parens = "\([^\)]*\)"

extract1 = PositionedText()
extract1.text = "_pattern1_"
extract1.span = range(3, 13)
extract1.text_before = "abc"
extract1.text_after = "defg(hij_p"

extract2 = PositionedText()
extract2.text = "_pattern2_"
extract2.span = range(21, 31)
extract2.text_before = "1_defg(hij"
extract2.text_after = "klmn)"

extract3 = PositionedText()
extract3.text = "(hij_pattern2_klmn)"
extract3.span = range(17, 36)
extract3.text_before = "tern1_defg"
extract3.text_after = ""


class PatternExtractionTestCase(unittest.TestCase):

    def _assert_positioned_texts_equal(self, expected, actual):
        self.assertEqual(expected.text, actual.text, "Texts differ")
        self.assertEqual(expected.span, actual.span, "Text spans  differ.")
        self.assertEqual(expected.text_before, actual.text_before, "Texts before pos differ.")
        self.assertEqual(expected.text_after, actual.text_after, "Texts after pos differ.")

    def test_simple_pattern(self):
        new_text, extracted_texts = extract(text_in, [pattern_simple])
        self.assertEqual(new_text, text_without_simple_pattern,
                         "Should have removed the simple pattern.")
        self.assertEqual(len(extracted_texts), 2)
        self._assert_positioned_texts_equal(extract1, extracted_texts[0])
        self._assert_positioned_texts_equal(extract2, extracted_texts[1])

        regex = re.compile(pattern_simple)
        new_text, extracted_texts = extract(text_in, [regex])
        self.assertEqual(new_text, text_without_simple_pattern,
                         "Should have removed the simple pattern using a regex.")
        self.assertEqual(len(extracted_texts), 2)
        self._assert_positioned_texts_equal(extract1, extracted_texts[0])
        self._assert_positioned_texts_equal(extract2, extracted_texts[1])

        new_text, extracted_texts = extract(text_in, [pattern_parens])
        self.assertEqual(new_text, text_without_paren_pattern,
                         "Should have removed the paren pattern.")
        self.assertEqual(len(extracted_texts), 1)
        self._assert_positioned_texts_equal(extract3, extracted_texts[0])

        regex = re.compile(pattern_parens)
        new_text, extracted_texts = extract(text_in, [regex])
        self.assertEqual(new_text, text_without_paren_pattern,
                         "Should have removed the paren pattern using a regex.")
        self.assertEqual(len(extracted_texts), 1)
        self._assert_positioned_texts_equal(extract3, extracted_texts[0])

    def test_multiple_patterns(self):
        patterns = [pattern_simple, pattern_parens]
        new_text, extracted_texts = extract(text_in, patterns)
        self.assertEqual(new_text, text_without_simple_and_paren_pattern,
                         "Should have removed both the simple and paren patterns.")

        patterns = [re.compile(pattern_simple), re.compile(pattern_parens)]
        new_text, extracted_texts = extract(text_in, patterns)
        self.assertEqual(new_text, text_without_simple_and_paren_pattern,
                         "Should have removed both the simple and paren patterns using regexes.")

    def test_empty_inputs(self):
        # should not raise an error on empty inputs
        new_text, extracts = extract("", [])
        self.assertEqual(new_text, "")
        self.assertEqual(extracts, [])
        new_text, extracts = extract("", [""])
        self.assertEqual(new_text, "")
        self.assertEqual(extracts, [])

    def test_bad_inputs(self):
        # should Raise on non-string input for first argument
        self.assertRaises(ValueError, extract, None, [])
        self.assertRaises(ValueError, extract, 23, [])
        self.assertRaises(ValueError, extract, {}, [])

        # should raise if 2nd arg is not an array of strings or regexps
        self.assertRaises(ValueError, extract, "", None)
        self.assertRaises(ValueError, extract, "", [None])
        self.assertRaises(ValueError, extract, "", [12, {}])


# These are variations on the output text from the extract()
# test above with xml-tags inserted in various positions.
integration_examples = {
    "xml1": "<t>abcdefg</t>",
    "xml2": "<t><m>a</m>b<n>c</n>d<o>e</o>f<p>g</p></t>",
    "xml3": "<t><m><n><o><p>a</p>bc</o>de</n>f</m>g</>",
    "xml4": "<t>a<m>bc<n>d<o>e<p>fg</m></n></o></p></t>"
}

integration_examples["verbose_xml"] = """
<doc
    some-attr="bla-bla"
    another-attr="1723"
>abc<self-closing-tag
    yet-another-attr="value"
/>def<some-tag
    foo="bar"
>g</some-tag></doc>
"""


class PatternIntegrationTestCase(unittest.TestCase):

    def test_integration_examples(self):
        for name, example in integration_examples.items():
            restored_text = integrate(example, [extract1, extract2, extract3])
            document = bs4.BeautifulSoup(restored_text, "html.parser")
            self.assertEqual(text_in, document.text, "Should restore text for example: " + name)


if __name__ == '__main__':
    unittest.main()
