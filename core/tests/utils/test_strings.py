import unittest
from PaperScraper.core.utils import strings


class TestStrings(unittest.TestCase):
    """Verifies that the strings module is working as expected"""

    def test_retitle(self):
        """Verifies that retitle works as expected"""

    def test_trim_string(self):
        """Tests that trim string functions as expected"""
        self.assertEqual("", strings.trim_string("", ""))
        self.assertEqual("", strings.trim_string("", "z"))
        self.assertEqual("", strings.trim_string("aaa", "a"))
        self.assertEqual("", strings.trim_string("aaaa", "a"))
        self.assertEqual("", strings.trim_string("baba", "ba"))
        self.assertEqual("baba", strings.trim_string("baba", "ab"))
        self.assertEqual("main", strings.trim_string("__main__", "_"))
        self.assertEqual("words", strings.trim_string("......words....", "."))
        self.assertEqual("TRING", strings.trim_string("STRING", "S"))
        self.assertEqual("TRING", strings.trim_string("STRINGS", "S"))
        self.assertEqual("TSRISNSG", strings.trim_string("STSRISNSGSSSS", "S"))
        self.assertEqual("azazaza", strings.trim_string("zazazazaz", "z"))
        self.assertEqual(" be or not to be?", strings.trim_string("to be or not to be?", "to"))
        self.assertEqual("to be or not to be?", strings.trim_string("  to be or not to be?  ", " "))

    def test_shorten(self):
        """Verifies that shorten works as intended"""
        self.assertEqual("", strings.shorten("any string", 0))
        self.assertEqual("any", strings.shorten("any string", 3))
        self.assertEqual("any", strings.shorten("any string", 4))
        self.assertEqual("any", strings.shorten("any string", 5))
        self.assertEqual("any...", strings.shorten("any string", 6))
        self.assertEqual(" ", strings.shorten(" ", 1))
        self.assertEqual("a", strings.shorten("aaa", 1))
        self.assertEqual("hello...", strings.shorten("hello world!", 8))
        self.assertEqual("hello al", strings.shorten("hello al", 8))
        self.assertEqual("he...", strings.shorten("hello al", 5))
        self.assertEqual("veryl...", strings.shorten("verylongword", 8))

        with self.assertRaises(IndexError):
            strings.shorten("", -1)
            strings.shorten("arbitrary string", -100)

    def test_title_case(self):
        """Verifies that title_case works as intended"""
        self.assertEqual("", strings.title_case(""))
        self.assertEqual("!!!", strings.title_case("!!!"))
        self.assertEqual("1234", strings.title_case("1234"))
        self.assertEqual("A234", strings.title_case("a234"))
        self.assertEqual("1word's", strings.title_case("1word's"))
        self.assertEqual("ALtErNaTiNg CaPs", strings.title_case("ALtErNaTiNg CaPs"))
        self.assertEqual("UPPERCASE STRING", strings.title_case("UPPERCASE STRING"))
        self.assertEqual("Lowercase String", strings.title_case("lowercase string"))
        self.assertEqual("Can't Contractions", strings.title_case("can't contractions"))
        self.assertEqual("String To Be Capitalized", strings.title_case("string to be capitalized"))
        self.assertEqual("Could've Should've Would've", strings.title_case("could've Should've would've"))

    def test_remove_invalid(self):
        """Tests that remove_invalid works as intended"""
        self.assertEqual("", strings.remove_invalid(""))
        self.assertEqual("", strings.remove_invalid("\\"))
        self.assertEqual("", strings.remove_invalid("/"))
        self.assertEqual("", strings.remove_invalid(":"))
        self.assertEqual("", strings.remove_invalid("*"))
        self.assertEqual("", strings.remove_invalid("?"))
        self.assertEqual("", strings.remove_invalid("<"))
        self.assertEqual("", strings.remove_invalid(">"))
        self.assertEqual("", strings.remove_invalid("|"))
        self.assertEqual("'", strings.remove_invalid('"'))
        self.assertEqual("'", strings.remove_invalid("'"))
        self.assertEqual("valid filename", strings.remove_invalid("valid filename"))
        self.assertEqual("invalid flename", strings.remove_invalid("invalid? f|lename"))

    def test_file_title(self):
        """Verifies that file_title works as intended"""
