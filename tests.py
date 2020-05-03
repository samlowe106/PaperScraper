import os
import shutil
import unittest
import app
# https://docs.python.org/3.8/library/unittest.html
# https://www.thepythoncode.com/article/extracting-image-metadata-in-python

"""
Unless otherwise stated, NONE of the URLs used for testing should be dead.
"""


class TestMainFunctions(unittest.TestCase):
    def test_count_parsed(self):
        self.assertEqual(0, app.submissionhelpers.is_parsed([]))
        self.assertEqual(1, app.submissionhelpers.is_parsed([("url string", True)]))
        self.assertEqual(3, app.submissionhelpers.is_parsed([("url1", True), ("url2", True), ("url3", True)]))
        self.assertEqual(0, app.submissionhelpers.is_parsed([("url1", False)]))
        self.assertEqual(2, app.submissionhelpers.is_parsed([("url1", True), ("url2", True), ("url3", False)]))

    
    def test_is_parsed(self):
        self.assertEqual(True, app.submissionhelpers.is_parsed([]))
        self.assertEqual(True, app.submissionhelpers.is_parsed([("url string", True)]))
        self.assertEqual(True, app.submissionhelpers.is_parsed([("url1", True), ("url2", True), ("url3", True)]))
        self.assertEqual(False, app.submissionhelpers.is_parsed([("url1", False)]))
        self.assertEqual(False, app.submissionhelpers.is_parsed([("url1", True), ("url2", True), ("url3", False)]))
    

    def test_sign_in(self):
        with self.assertRaises(ConnectionError):
            app.main.sign_in("", "")

    """
    def test_is_skippable(self):
        self.assertEqual(True, False)
    """

    def test_is_recognized(self):
        self.assertTrue(app.main.is_recognized(".png"))
        self.assertTrue(app.main.is_recognized(".PnG"))
        self.assertTrue(app.main.is_recognized(".PNG"))
        self.assertTrue(app.main.is_recognized(".jpg"))
        self.assertTrue(app.main.is_recognized(".jpeg"))
        self.assertTrue(app.main.is_recognized(".png"))
        self.assertFalse(app.main.is_recognized("bar"))
        self.assertFalse(app.main.is_recognized(".foo"))
        self.assertFalse(app.main.is_recognized("arbitrary"))


class TestFileHelpers(unittest.TestCase):
    def test_create_directory(self):
        # Establish test dir
        test_dir = "test_dir"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        os.chdir(test_dir)

        app.filehelpers.create_directory("directory1")
        self.assertTrue("directory1" in os.listdir(os.getcwd()))

        # Creating a second directory with the same name shouldn't do anything
        app.filehelpers.create_directory("directory1")
        self.assertTrue("directory1" in os.listdir(os.getcwd()))

        app.filehelpers.create_directory("directory2")
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
            app.urlhelpers.download_file(urls_sizes[i][0], test_dir, str(i))
            # Assert that the downloaded file is the same size as expected
            self.assertEqual(urls_sizes[i][1], os.path.getsize(os.path.join(test_dir, str(i) + ".jpg")))

        # Remove test directory
        shutil.rmtree(test_dir)


    def test_get_file_extension(self):
        self.assertEqual("", app.filehelpers.get_file_extension(""))
        self.assertEqual("", app.filehelpers.get_file_extension("Z:"))
        self.assertEqual("", app.filehelpers.get_file_extension("a"))
        self.assertEqual("", app.filehelpers.get_file_extension("oneword"))
        self.assertEqual("", app.filehelpers.get_file_extension("hi"))
        self.assertEqual("", app.filehelpers.get_file_extension("invalid string"))
        self.assertEqual("", app.filehelpers.get_file_extension("path\\folder"))
        self.assertEqual("", app.filehelpers.get_file_extension("www.website.com/webpage"))
        self.assertEqual(".jpg", app.filehelpers.get_file_extension("C:\\path\\file.jpg"))
        self.assertEqual(".png", app.filehelpers.get_file_extension("J:\\path\\F.PNG"))
        self.assertEqual(".pdf", app.filehelpers.get_file_extension("L:\\paper...jpg.PDF"))
        self.assertEqual(".xml", app.filehelpers.get_file_extension("www.site.com/file.xml?querystring"))
        self.assertEqual(".foo", app.filehelpers.get_file_extension("www.site.com/file.foo?q1?q2"))
        self.assertEqual(".jpeg", app.filehelpers.get_file_extension("www.website.com/file.jpeg"))


class TestStrHelpers(unittest.TestCase):
    def test_trim_string(self):
        self.assertEqual("", app.strhelpers.trim_string("", ""))
        self.assertEqual("", app.strhelpers.trim_string("", "z"))
        self.assertEqual("", app.strhelpers.trim_string("aaa", "a"))
        self.assertEqual("", app.strhelpers.trim_string("aaaa", "a"))
        self.assertEqual("", app.strhelpers.trim_string("baba", "ba"))
        self.assertEqual("baba", app.strhelpers.trim_string("baba", "ab"))
        self.assertEqual("main", app.strhelpers.trim_string("__main__", "_"))
        self.assertEqual("words", app.strhelpers.trim_string("......words....", "."))
        self.assertEqual("TRING", app.strhelpers.trim_string("STRING", "S"))
        self.assertEqual("TRING", app.strhelpers.trim_string("STRINGS", "S"))
        self.assertEqual("TSRISNSG", app.strhelpers.trim_string("STSRISNSGSSSS", "S"))
        self.assertEqual("azazaza", app.strhelpers.trim_string("zazazazaz", "z"))
        self.assertEqual(" be or not to be?", app.strhelpers.trim_string("to be or not to be?", "to"))
        self.assertEqual("to be or not to be?", app.strhelpers.trim_string("  to be or not to be?  ", " "))
        
    def test_file_title(self):
        self.assertEqual("", app.strhelpers.file_title(""))
        self.assertEqual("", app.strhelpers.file_title("\\"))
        self.assertEqual("", app.strhelpers.file_title("/"))
        self.assertEqual("", app.strhelpers.file_title(":"))
        self.assertEqual("", app.strhelpers.file_title("*"))
        self.assertEqual("", app.strhelpers.file_title("?"))
        self.assertEqual("", app.strhelpers.file_title("<"))
        self.assertEqual("", app.strhelpers.file_title(">"))
        self.assertEqual("", app.strhelpers.file_title("|"))
        self.assertEqual("'", app.strhelpers.file_title('"'))
        self.assertEqual("'", app.strhelpers.file_title("'"))
        self.assertEqual("valid filename", app.strhelpers.file_title("valid filename"))
        self.assertEqual("invalid flename", app.strhelpers.file_title("invalid? f|lename"))

    """
    def test_retitle(self):
        self.assertEqual(True, False)
    """

    def test_shorten(self):
        self.assertEqual("", app.strhelpers.shorten("", 0))
        self.assertEqual("", app.strhelpers.shorten("", 100))
        self.assertEqual("", app.strhelpers.shorten("any string of any length", 0))
        self.assertEqual("any string", app.strhelpers.shorten("any string of any length", 10))
        self.assertEqual("VeryLongOn", app.strhelpers.shorten("VeryLongOneWordString", 10))
        self.assertEqual("this string of", app.strhelpers.shorten("this string of this length", 15))
        self.assertEqual("ANOTHER multi.word", app.strhelpers.shorten("ANOTHER multi.word string!!!", 20))
        self.assertEqual("VeryLongOneWordString", app.strhelpers.shorten("VeryLongOneWordString", 300))
        self.assertEqual("any string less than 300", app.strhelpers.shorten("any string less than 300", 300))
        

        with self.assertRaises(IndexError):
            app.strhelpers.shorten("", -1)
            app.strhelpers.shorten("arbitrary string", -100)

    def test_attempt_shorten(self):

        # TODO: test cases where splitter != " "
        self.assertEqual("", app.strhelpers.attempt_shorten("", "", 0))
        self.assertEqual("", app.strhelpers.attempt_shorten("", "", 100))
        self.assertEqual("", app.strhelpers.attempt_shorten("any string of any length", "9", 0))
        self.assertEqual("any string", app.strhelpers.attempt_shorten("any string of this length", " ", 10))
        self.assertEqual("this string of", app.strhelpers.attempt_shorten("this string of this length", " ", 15))
        self.assertEqual("ANOTHER multi.word", app.strhelpers.attempt_shorten("ANOTHER multi.word string!!!", " ", 20))
        self.assertEqual("VeryLongOneWordString", app.strhelpers.attempt_shorten("VeryLongOneWordString", " ",300))
        self.assertEqual("VeryLongOneWordString", app.strhelpers.attempt_shorten("VeryLongOneWordString", " ", 10))
        self.assertEqual("any string less than 300", app.strhelpers.attempt_shorten("any string less than 300", " ", 300))
        

        with self.assertRaises(IndexError):
            app.strhelpers.attempt_shorten("", "", -1)
            app.strhelpers.attempt_shorten("arbitrary string", " ", -100)
            
    def test_title_case(self):
        self.assertEqual("", app.strhelpers.title_case(""))
        self.assertEqual("!!!", app.strhelpers.title_case("!!!"))
        self.assertEqual("1234", app.strhelpers.title_case("1234"))
        self.assertEqual("A234", app.strhelpers.title_case("a234"))
        self.assertEqual("1word's", app.strhelpers.title_case("1word's"))
        self.assertEqual("ALtErNaTiNg CaPs", app.strhelpers.title_case("ALtErNaTiNg CaPs"))
        self.assertEqual("UPPERCASE STRING", app.strhelpers.title_case("UPPERCASE STRING"))
        self.assertEqual("Lowercase String", app.strhelpers.title_case("lowercase string"))
        self.assertEqual("Can't Contractions", app.strhelpers.title_case("can't contractions"))
        self.assertEqual("String To Be Capitalized", app.strhelpers.title_case("string to be capitalized"))
        self.assertEqual("Could've Should've Would've", app.strhelpers.title_case("could've Should've would've"))


if __name__ == '__main__':
    unittest.main()
