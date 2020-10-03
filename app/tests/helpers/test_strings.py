import helpers.strings


def test_trim_string(self):
    self.assertEqual("", helpers.strhelpers.trim_string("", ""))
    self.assertEqual("", helpers.strhelpers.trim_string("", "z"))
    self.assertEqual("", helpers.strhelpers.trim_string("aaa", "a"))
    self.assertEqual("", helpers.strhelpers.trim_string("aaaa", "a"))
    self.assertEqual("", helpers.strhelpers.trim_string("baba", "ba"))
    self.assertEqual("baba", helpers.strhelpers.trim_string("baba", "ab"))
    self.assertEqual("main", helpers.strhelpers.trim_string("__main__", "_"))
    self.assertEqual("words", helpers.strhelpers.trim_string("......words....", "."))
    self.assertEqual("TRING", helpers.strhelpers.trim_string("STRING", "S"))
    self.assertEqual("TRING", helpers.strhelpers.trim_string("STRINGS", "S"))
    self.assertEqual("TSRISNSG", helpers.strhelpers.trim_string("STSRISNSGSSSS", "S"))
    self.assertEqual("azazaza", helpers.strhelpers.trim_string("zazazazaz", "z"))
    self.assertEqual(" be or not to be?", helpers.strhelpers.trim_string("to be or not to be?", "to"))
    self.assertEqual("to be or not to be?", helpers.strhelpers.trim_string("  to be or not to be?  ", " "))
    

def test_file_title(self):
    self.assertEqual("", helpers.filehelpers.remove_invalid(""))
    self.assertEqual("", helpers.filehelpers.remove_invalid("\\"))
    self.assertEqual("", helpers.filehelpers.remove_invalid("/"))
    self.assertEqual("", helpers.filehelpers.remove_invalid(":"))
    self.assertEqual("", helpers.filehelpers.remove_invalid("*"))
    self.assertEqual("", helpers.filehelpers.remove_invalid("?"))
    self.assertEqual("", helpers.filehelpers.remove_invalid("<"))
    self.assertEqual("", helpers.filehelpers.remove_invalid(">"))
    self.assertEqual("", helpers.filehelpers.remove_invalid("|"))
    self.assertEqual("'", helpers.filehelpers.remove_invalid('"'))
    self.assertEqual("'", helpers.filehelpers.remove_invalid("'"))
    self.assertEqual("valid filename", helpers.filehelpers.remove_invalid("valid filename"))
    self.assertEqual("invalid flename", helpers.filehelpers.remove_invalid("invalid? f|lename"))

"""
def test_retitle(self):
    self.assertEqual(True, False)
"""

def test_shorten(self):
    self.assertEqual("", helpers.strhelpers.shorten("any string", 0))
    self.assertEqual("any", helpers.strhelpers.shorten("any string", 3))
    self.assertEqual("any", helpers.strhelpers.shorten("any string", 4))
    self.assertEqual("any", helpers.strhelpers.shorten("any string", 5))
    self.assertEqual("any...", helpers.strhelpers.shorten("any string", 6))
    self.assertEqual(" ", helpers.strhelpers.shorten(" ", 1))
    self.assertEqual("a", helpers.strhelpers.shorten("aaa", 1))
    self.assertEqual("hello...", helpers.strhelpers.shorten("hello world!", 8))
    self.assertEqual("hello al", helpers.strhelpers.shorten("hello al", 8))
    self.assertEqual("he...", helpers.strhelpers.shorten("hello al", 5))
    self.assertEqual("veryl...", helpers.strhelpers.shorten("verylongword", 8))
    
    with self.assertRaises(IndexError):
        helpers.strhelpers.shorten("", -1)
        helpers.strhelpers.shorten("arbitrary string", -100)


def test_title_case(self):
    self.assertEqual("", helpers.strhelpers.title_case(""))
    self.assertEqual("!!!", helpers.strhelpers.title_case("!!!"))
    self.assertEqual("1234", helpers.strhelpers.title_case("1234"))
    self.assertEqual("A234", helpers.strhelpers.title_case("a234"))
    self.assertEqual("1word's", helpers.strhelpers.title_case("1word's"))
    self.assertEqual("ALtErNaTiNg CaPs", helpers.strhelpers.title_case("ALtErNaTiNg CaPs"))
    self.assertEqual("UPPERCASE STRING", helpers.strhelpers.title_case("UPPERCASE STRING"))
    self.assertEqual("Lowercase String", helpers.strhelpers.title_case("lowercase string"))
    self.assertEqual("Can't Contractions", helpers.strhelpers.title_case("can't contractions"))
    self.assertEqual("String To Be Capitalized", helpers.strhelpers.title_case("string to be capitalized"))
    self.assertEqual("Could've Should've Would've", helpers.strhelpers.title_case("could've Should've would've"))
