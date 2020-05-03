import os
import shutil
import unittest
from app.main import count_parsed, is_parsed, sign_in, is_skippable 
from app.imagehelpers import create_directory, convert_file, download_image, find_urls, get_extension, parse_imgur_album, parse_imgur_single
from app.strhelpers import trim_string, file_title, retitle, shorten, attempt_shorten, title_case
# https://docs.python.org/3.8/library/unittest.html
# https://www.thepythoncode.com/article/extracting-image-metadata-in-python

"""
Unless otherwise stated, NONE of the URLs used for testing should be dead.
"""


class TestMainFunctions(unittest.TestCase):
    def test_count_parsed(self):
        self.assertEqual(0, is_parsed([]))
        self.assertEqual(1, is_parsed([("url string", True)]))
        self.assertEqual(3, is_parsed([("url1", True), ("url2", True), ("url3", True)]))
        self.assertEqual(0, is_parsed([("url1", False)]))
        self.assertEqual(2, is_parsed([("url1", True), ("url2", True), ("url3", False)]))

    
    def test_is_parsed(self):
        self.assertEqual(True, is_parsed([]))
        self.assertEqual(True, is_parsed([("url string", True)]))
        self.assertEqual(True, is_parsed([("url1", True), ("url2", True), ("url3", True)]))
        self.assertEqual(False, is_parsed([("url1", False)]))
        self.assertEqual(False, is_parsed([("url1", True), ("url2", True), ("url3", False)]))
    

    def test_sign_in(self):
        with self.assertRaises(ConnectionError):
            sign_in("", "")

    """
    def test_is_skippable(self):
        self.assertEqual(True, False)
    """


class TestImageHelpers(unittest.TestCase):
    def test_create_directory(self):
        # Establish test dir
        test_dir = "test_dir"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        os.chdir(test_dir)

        create_directory("directory1")
        self.assertTrue("directory1" in os.listdir(os.getcwd()))

        # Creating a second directory with the same name shouldn't do anything
        create_directory("directory1")
        self.assertTrue("directory1" in os.listdir(os.getcwd()))

        create_directory("directory2")
        self.assertTrue("directory2" in os.listdir(os.getcwd()))

        # Remove test directory
        os.chdir("..")
        shutil.rmtree(test_dir)

    """
    def test_convert_to_png(self):
        self.assertEqual(True, False)

    def test_save_images(self):
        self.assertEqual(True, False)

    def test_parse_imgur_album(self):
        self.assertEqual(True, False)

    def test_parse_imgur_single(self):
        self.assertEqual(True, False)

    def test_find_urls(self):
        self.assertEqual(True, False)
    """

    def test_download_image(self):
        # Establish test dir
        test_dir = "test_dir"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        
        # List of tuples in the form
        #  url, expected size (NOT size on disk) in bytes
        urls_sizes = [("https://i.redd.it/qqgds2i3ueh31.jpg", 2519027),
                      ("https://i.redd.it/mfqm1x49akgy.jpg", 838598),
                      ("https://i.redd.it/jh0gfb3ktvkz.jpg", 467577),
                      ("https://i.imgur.com/ppqan5G.jpg", 2846465),
                      ("https://i.imgur.com/CS8QhJG.jpg", 3336288),
                      ("https://i.imgur.com/B6HPXkk.jpg", 958843)
        ]

        for i in range(len(urls_sizes)):
            download_image(urls_sizes[i][0], test_dir, str(i))
            # Assert that the downloaded file is the same size as expected
            self.assertEqual(urls_sizes[i][1], os.path.getsize(os.path.join(test_dir, str(i) + ".jpg")))

        # Remove test directory
        shutil.rmtree(test_dir)


    def test_get_extension(self):
        self.assertEqual("", get_extension(""))
        self.assertEqual("", get_extension("Z:"))
        self.assertEqual("", get_extension("a"))
        self.assertEqual("", get_extension("oneword"))
        self.assertEqual("", get_extension("hi"))
        self.assertEqual("", get_extension("invalid string"))
        self.assertEqual("", get_extension("path\\folder"))
        self.assertEqual("", get_extension("www.website.com/webpage"))
        self.assertEqual(".jpg", get_extension("C:\\path\\file.jpg"))
        self.assertEqual(".png", get_extension("J:\\path\\F.PNG"))
        self.assertEqual(".pdf", get_extension("L:\\paper...jpg.PDF"))
        self.assertEqual(".xml", get_extension("www.site.com/file.xml?querystring"))
        self.assertEqual(".foo", get_extension("www.site.com/file.foo?q1?q2"))
        self.assertEqual(".jpeg", get_extension("www.website.com/file.jpeg"))


class TestStringHelpers(unittest.TestCase):
    def test_trim_string(self):
        self.assertEqual("", trim_string("", ""))
        self.assertEqual("", trim_string("", "z"))
        self.assertEqual("", trim_string("aaa", "a"))
        self.assertEqual("", trim_string("aaaa", "a"))
        self.assertEqual("", trim_string("baba", "ba"))
        self.assertEqual("baba", trim_string("baba", "ab"))
        self.assertEqual("main", trim_string("__main__", "_"))
        self.assertEqual("words", trim_string("......words....", "."))
        self.assertEqual("TRING", trim_string("STRING", "S"))
        self.assertEqual("TRING", trim_string("STRINGS", "S"))
        self.assertEqual("TSRISNSG", trim_string("STSRISNSGSSSS", "S"))
        self.assertEqual("azazaza", trim_string("zazazazaz", "z"))
        self.assertEqual(" be or not to be?", trim_string("to be or not to be?", "to"))
        self.assertEqual("to be or not to be?", trim_string("  to be or not to be?  ", " "))
        
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
        self.assertEqual("", shorten("", 0))
        self.assertEqual("", shorten("", 100))
        self.assertEqual("", shorten("any string of any length", 0))
        self.assertEqual("any string", shorten("any string of any length", 10))
        self.assertEqual("VeryLongOn", shorten("VeryLongOneWordString", 10))
        self.assertEqual("this string of", shorten("this string of this length", 15))
        self.assertEqual("ANOTHER multi.word", shorten("ANOTHER multi.word string!!!", 20))
        self.assertEqual("VeryLongOneWordString", shorten("VeryLongOneWordString", 300))
        self.assertEqual("any string less than 300", shorten("any string less than 300", 300))
        

        with self.assertRaises(IndexError):
            shorten("", -1)
            shorten("arbitrary string", -100)

    def test_attempt_shorten(self):

        # TODO: test cases where splitter != " "
        self.assertEqual("", attempt_shorten("", "", 0))
        self.assertEqual("", attempt_shorten("", "", 100))
        self.assertEqual("", attempt_shorten("any string of any length", "9", 0))
        self.assertEqual("any string", attempt_shorten("any string of this length", " ", 10))
        self.assertEqual("this string of", attempt_shorten("this string of this length", " ", 15))
        self.assertEqual("ANOTHER multi.word", attempt_shorten("ANOTHER multi.word string!!!", " ", 20))
        self.assertEqual("VeryLongOneWordString", attempt_shorten("VeryLongOneWordString", " ",300))
        self.assertEqual("VeryLongOneWordString", attempt_shorten("VeryLongOneWordString", " ", 10))
        self.assertEqual("any string less than 300", attempt_shorten("any string less than 300", " ", 300))
        

        with self.assertRaises(IndexError):
            attempt_shorten("", "", -1)
            attempt_shorten("arbitrary string", " ", -100)
            
    def test_title_case(self):
        self.assertEqual("", title_case(""))
        self.assertEqual("!!!", title_case("!!!"))
        self.assertEqual("1234", title_case("1234"))
        self.assertEqual("A234", title_case("a234"))
        self.assertEqual("1word's", title_case("1word's"))
        self.assertEqual("ALtErNaTiNg CaPs", title_case("ALtErNaTiNg CaPs"))
        self.assertEqual("UPPERCASE STRING", title_case("UPPERCASE STRING"))
        self.assertEqual("Lowercase String", title_case("lowercase string"))
        self.assertEqual("Can't Contractions", title_case("can't contractions"))
        self.assertEqual("String To Be Capitalized", title_case("string to be capitalized"))
        self.assertEqual("Could've Should've Would've", title_case("could've Should've would've"))


if __name__ == '__main__':
    unittest.main()
