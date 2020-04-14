import unittest
from app.main import is_skippable
from app.filehelpers import *
from app.strhelpers import *
from app.imagehelpers import *
# https://docs.python.org/3.8/library/unittest.html


class TestStringHelpers(unittest.TestCase):
    def test_trim_string(self):
        self.assertEqual("", trim_string("", ""))
        self.assertEqual("", trim_string("", "z"))
        self.assertEqual("", trim_string("aaa", "a"))
        self.assertEqual("", trim_string("aaaa", "a"))
        self.assertEqual("", trim_string("baba", "ba"))
        self.assertEqual("baba", trim_string("baba", "ab"))
        self.assertEqual("main", trim_string("__main__", "_"))
        self.assertEqual("TRING", trim_string("STRING", "S"))
        self.assertEqual("TRING", trim_string("STRINGS", "S"))
        self.assertEqual("TSRISNSG", trim_string("STSRISNSGSSSS", "S"))
        self.assertEqual("azazaza", trim_string("zazazazaz", "z"))
        self.assertEqual(" be or not to be?", trim_string("to be or not to be?", "to"))
        self.assertEqual("to be or not to be?", trim_string("  to be or not to be?  ", " "))
        self.assertEqual("words", trim_string("......words....", "."))

    def test_file_title(self):
        self.assertEqual("", file_title(""))
        self.assertEqual("", file_title("\\"))
        self.assertEqual("", file_title("/"))
        self.assertEqual("", file_title(":"))
        self.assertEqual("", file_title("*"))
        self.assertEqual("", file_title("?"))
        self.assertEqual("", file_title("<"))
        self.assertEqual("", file_title(">"))
        self.assertEqual("", file_title("|"))
        self.assertEqual("'", file_title('"'))
        self.assertEqual("'", file_title("'"))
        self.assertEqual("valid filename", file_title("valid filename"))
        self.assertEqual("invalid flename", file_title("invalid? f|lename"))

    """
    def test_retitle(self):
        self.assertEqual(True, False)
    """

    def test_shorten(self):
        self.assertEqual("",
                         shorten("", 0))
        self.assertEqual("",
                         shorten("", 100))
        self.assertEqual("",
                         shorten("any string of any length", 0))
        self.assertEqual("this string of",
                         shorten("this string of this length", 15))
        self.assertEqual("any string",
                         shorten("any string of any length", 10))
        self.assertEqual("any string less than 300",
                         shorten("any string less than 300", 300))
        self.assertEqual("VeryLongOneWordString",
                         shorten("VeryLongOneWordString", 300))
        self.assertEqual("VeryLongOn",
                         shorten("VeryLongOneWordString", 10))
        self.assertEqual("ANOTHER multi.word",
                         shorten("ANOTHER multi.word string!!!", 20))

        with self.assertRaises(IndexError):
            shorten("", -1)
            shorten("arbitrary string", -100)

    def test_attempt_shorten(self):

        # TODO: test cases where splitter != " "
        self.assertEqual("",
                         attempt_shorten("", "", 0))
        self.assertEqual("",
                         attempt_shorten("", "", 100))
        self.assertEqual("",
                         attempt_shorten("any string of any length", "9", 0))
        self.assertEqual("this string of",
                         attempt_shorten("this string of this length", " ", 15))
        self.assertEqual("any string",
                         attempt_shorten("any string of this length", " ", 10))
        self.assertEqual("any string less than 300",
                         attempt_shorten("any string less than 300", " ", 300))
        self.assertEqual("VeryLongOneWordString",
                         attempt_shorten("VeryLongOneWordString", " ",300))
        self.assertEqual("VeryLongOneWordString",
                         attempt_shorten("VeryLongOneWordString", " ", 10))
        self.assertEqual("ANOTHER multi.word",
                         attempt_shorten("ANOTHER multi.word string!!!", " ", 20))

        with self.assertRaises(IndexError):
            attempt_shorten("", "", -1)
            attempt_shorten("arbitrary string", " ", -100)
            
    def test_title_case(self):
        self.assertEqual("",
                         title_case(""))
        self.assertEqual("String To Be Capitalized",
                         title_case("string to be capitalized"))
        self.assertEqual("UPPERCASE STRING",
                         title_case("UPPERCASE STRING"))
        self.assertEqual("Lowercase String",
                         title_case("lowercase string"))
        self.assertEqual("Can't Contractions",
                         title_case("can't contractions"))
        self.assertEqual("1word's",
                         title_case("1word's"))
        self.assertEqual("1234",
                         title_case("1234"))
        self.assertEqual("A234",
                         title_case("a234"))
        self.assertEqual("Could've Should've Would've",
                         title_case("could've Should've would've"))
        self.assertEqual("!!!",
                         title_case("!!!"))
        self.assertEqual("ALtErNaTiNg CaPs",
                         title_case("ALtErNaTiNg CaPs"))


class TestFileHelpers(unittest.TestCase):
    """
    def test_create_directory(self):
        self.assertEqual(True, False)

    def test_convert_to_png(self):
        self.assertEqual(True, False)

    def test_save_images(self):
        self.assertEqual(True, False)
    """


class TestImageHelpers(unittest.TestCase):
    """
    def test_parse_imgur_album(self):
        self.assertEqual(True, False)

    def test_parse_imgur_single(self):
        self.assertEqual(True, False)

    def test_find_urls(self):
        self.assertEqual(True, False)

    def test_download_image(self):
        self.assertEqual(True, False)
    """

    def test_get_extension(self):
        self.assertEqual("",
                         get_extension(""))
        self.assertEqual("",
                         get_extension("Z:"))
        self.assertEqual("",
                         get_extension("a"))
        self.assertEqual("",
                         get_extension("oneword"))
        self.assertEqual("",
                         get_extension("hi"))
        self.assertEqual("",
                         get_extension("invalid string"))
        self.assertEqual("",
                         get_extension("path\\folder"))
        self.assertEqual("",
                         get_extension("www.website.com/webpage"))
        self.assertEqual(".jpg",
                         get_extension("C:\\path\\file.jpg"))
        self.assertEqual(".png",
                         get_extension("J:\\path\\F.PNG"))
        self.assertEqual(".pdf",
                         get_extension("L:\\paper...jpg.PDF"))
        self.assertEqual(".jpeg",
                         get_extension("www.website.com/file.jpeg"))
        self.assertEqual(".xml",
                         get_extension("www.site.com/file.xml?querystring"))
        self.assertEqual(".foo",
                         get_extension("www.site.com/file.foo?q1?q2"))


class TestMainFunctions(unittest.TestCase):
    """
    def test_is_skippable(self):
        self.assertEqual(True, False)
    """


if __name__ == '__main__':
    unittest.main()
