import app.filehelpers
import app.strhelpers
import app.urlhelpers
import main
import os
import requests
import shutil
import unittest
# https://www.thepythoncode.com/article/extracting-image-metadata-in-python

""" Unless otherwise stated, NONE of the URLs used for testing should be dead. """


class TestMainFunctions(unittest.TestCase):

    def test_sign_in(self):
        with self.assertRaises(ConnectionError):
            main.sign_in("", "")

    """
    def test_is_skippable(self):
        self.assertEqual(True, False)
    """

    def test_count_parsed(self):
        self.assertEqual(0, main.count_parsed([]))
        self.assertEqual(1, main.count_parsed([("url string", True)]))
        self.assertEqual(3, main.count_parsed([("url1", True), ("url2", True), ("url3", True)]))
        self.assertEqual(0, main.count_parsed([("url1", False)]))
        self.assertEqual(2, main.count_parsed([("url1", True), ("url2", True), ("url3", False)]))

    
    def test_is_parsed(self):
        self.assertEqual(True, main.is_parsed([]))
        self.assertEqual(True, main.is_parsed([("url string", True)]))
        self.assertEqual(True, main.is_parsed([("url1", True), ("url2", True), ("url3", True)]))
        self.assertEqual(False, main.is_parsed([("url1", False)]))
        self.assertEqual(False, main.is_parsed([("url1", True), ("url2", True), ("url3", False)]))


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


    def test_prevent_collisions(self):
        pass

    """
    def test_convert_file(self):
        self.assertEqual(True, False)
    """


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
        self.assertEqual("", app.filehelpers.remove_invalid(""))
        self.assertEqual("", app.filehelpers.remove_invalid("\\"))
        self.assertEqual("", app.filehelpers.remove_invalid("/"))
        self.assertEqual("", app.filehelpers.remove_invalid(":"))
        self.assertEqual("", app.filehelpers.remove_invalid("*"))
        self.assertEqual("", app.filehelpers.remove_invalid("?"))
        self.assertEqual("", app.filehelpers.remove_invalid("<"))
        self.assertEqual("", app.filehelpers.remove_invalid(">"))
        self.assertEqual("", app.filehelpers.remove_invalid("|"))
        self.assertEqual("'", app.filehelpers.remove_invalid('"'))
        self.assertEqual("'", app.filehelpers.remove_invalid("'"))
        self.assertEqual("valid filename", app.filehelpers.remove_invalid("valid filename"))
        self.assertEqual("invalid flename", app.filehelpers.remove_invalid("invalid? f|lename"))

    """
    def test_retitle(self):
        self.assertEqual(True, False)
    """

    """ TODO: UPDATE
    def test_shorten(self):
        self.assertEqual("", app.strhelpers.shorten("", 0))
        self.assertEqual("", app.strhelpers.shorten("", 100))
        self.assertEqual("", app.strhelpers.shorten("any string of any length", 0))
        self.assertEqual("any str...", app.strhelpers.shorten("any string of any length", 10))
        self.assertEqual("VeryLon...", app.strhelpers.shorten("VeryLongOneWordString", 10))
        self.assertEqual("this string of", app.strhelpers.shorten("this string of this length", 15))
        self.assertEqual("ANOTHER multi.word", app.strhelpers.shorten("ANOTHER multi.word string!!!", 20))
        self.assertEqual("VeryLongOneWordString", app.strhelpers.shorten("VeryLongOneWordString", 300))
        self.assertEqual("any string less than 300", app.strhelpers.shorten("any string less than 300", 300))

        with self.assertRaises(IndexError):
            app.strhelpers.shorten("", -1)
            app.strhelpers.shorten("arbitrary string", -100)
        """


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


class TestURLHelpers(unittest.TestCase):
    

    def test_recognized(self):
        self.assertTrue(app.urlhelpers.recognized(".png"))
        self.assertTrue(app.urlhelpers.recognized(".PnG"))
        self.assertTrue(app.urlhelpers.recognized(".PNG"))
        self.assertTrue(app.urlhelpers.recognized(".jpg"))
        self.assertTrue(app.urlhelpers.recognized(".jpeg"))
        self.assertTrue(app.urlhelpers.recognized(".gif"))
        self.assertFalse(app.urlhelpers.recognized("bar"))
        self.assertFalse(app.urlhelpers.recognized(".foo"))
        self.assertFalse(app.urlhelpers.recognized("arbitrary"))
        self.assertFalse(app.urlhelpers.recognized("gif"))
        self.assertFalse(app.urlhelpers.recognized("png"))
        self.assertFalse(app.urlhelpers.recognized("file.png"))


    def test_parse_imgur_album(self):
        self.assertEqual(["https://i.imgur.com/NVQ1nuu.png",
                          "https://i.imgur.com/rDQ6BEA.jpg",
                          "https://i.imgur.com/gIMtb0Z.png",
                          "https://i.imgur.com/GeZmbJA.png",
                          "https://i.imgur.com/AGWHnX0.jpg",
                          "https://i.imgur.com/yt86fMB.jpg",
                          "https://i.imgur.com/cG9eXMk.jpg",
                          "https://i.imgur.com/4gdcscj.jpg",
                          "https://i.imgur.com/uA1NSv3.png"],
                          app.urlhelpers.parse_imgur_album("https://imgur.com/a/rSZlZ"))
        
        self.assertEqual(["https://i.imgur.com/oPXMrnr.png",
                          "https://i.imgur.com/Au8PAtj.png"],
                          app.urlhelpers.parse_imgur_album("https://imgur.com/gallery/NXBcU"))
        
        self.assertEqual(["https://i.imgur.com/zkREZI9.jpg",
                          "https://i.imgur.com/Qj7oouc.jpg",
                          "https://i.imgur.com/EthO1mq.jpg",
                          "https://i.imgur.com/xD1f2tb.jpg",
                          "https://i.imgur.com/TGMnQ51.jpg",
                          "https://i.imgur.com/3EXJq2A.jpg",
                          "https://i.imgur.com/KREPkFn.jpg",
                          "https://i.imgur.com/rc0ZVRv.jpg",
                          "https://i.imgur.com/G9pYJ0J.jpg",
                          "https://i.imgur.com/n4YRzTE.jpg",
                          "https://i.imgur.com/MU26NEH.jpg",
                          "https://i.imgur.com/NrmQqQt.jpg",
                          "https://i.imgur.com/iJBMppF.jpg",
                          "https://i.imgur.com/Id2wt99.jpg",
                          "https://i.imgur.com/It96Qrx.jpg"],
                          app.urlhelpers.parse_imgur_album("https://imgur.com/a/uZJHE"))
        

    def test_parse_imgur_single(self):
        self.assertEqual("https://i.imgur.com/jTAD7G1.jpg",
                         app.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/jTAD7G1"))
        self.assertEqual("https://i.imgur.com/WVntmOE.jpg",
                         app.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/WVntmOE"))
        self.assertEqual("https://i.imgur.com/rzOOFgI.jpg",
                         app.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/rzOOFgI"))
        self.assertEqual("https://i.imgur.com/mtjTo2o.jpg",
                         app.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/mtjTo2o"))
        self.assertEqual("https://i.imgur.com/mgfgDYb.jpg",
                         app.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/mgfgDYb"))


    def test_get_extension(self):
        url_extension = [
            ("https://cdnb.artstation.com/p/assets/images/images/026/326/667/large/eddie-mendoza-last-train.jpg?1588487140", ".jpeg"),
            ("https://cdnb.artstation.com/p/assets/images/images/026/292/247/large/jessie-lam-acv-ladyeivortweaks.jpg?1588382308", ".jpeg"),
            ("https://i.imgur.com/l8EbNfy.jpg", ".jpeg"),
            ("https://i.imgur.com/oPXMrnr.png", ".png"),
            ("https://i.imgur.com/GeZmbJA.png", ".png")
        ]

        for url, extension in url_extension:
            r = requests.get(url)
            if r.status_code == 200:
                self.assertEqual(extension, app.urlhelpers.get_extension(r))


    def test_find_urls(self):
        url_tups = [("https://imgur.com/a/rSZlZ",              ["https://i.imgur.com/NVQ1nuu.png",
                                                                "https://i.imgur.com/rDQ6BEA.jpg",
                                                                "https://i.imgur.com/gIMtb0Z.png",
                                                                "https://i.imgur.com/GeZmbJA.png",
                                                                "https://i.imgur.com/AGWHnX0.jpg",
                                                                "https://i.imgur.com/yt86fMB.jpg",
                                                                "https://i.imgur.com/cG9eXMk.jpg",
                                                                "https://i.imgur.com/4gdcscj.jpg",
                                                                "https://i.imgur.com/uA1NSv3.png"]),
                    ("https://imgur.com/gallery/NXBcU",        ["https://i.imgur.com/oPXMrnr.png",
                                                                "https://i.imgur.com/Au8PAtj.png"]),
                    ("https://imgur.com/r/Wallpapers/jTAD7G1", ["https://i.imgur.com/jTAD7G1.jpg"]),
                    ("https://imgur.com/r/Wallpapers/WVntmOE", ["https://i.imgur.com/WVntmOE.jpg"]),
                    ("https://imgur.com/r/Wallpapers/rzOOFgI", ["https://i.imgur.com/rzOOFgI.jpg"]),
                    ("https://imgur.com/r/Wallpapers/mtjTo2o", ["https://i.imgur.com/mtjTo2o.jpg"]),
                    ("https://imgur.com/r/Wallpapers/mgfgDYb", ["https://i.imgur.com/mgfgDYb.jpg"])
        ]
        
        for url, expected in url_tups:
            r = requests.get(url)
            if r.status_code == 200:
                self.assertEqual(expected, app.urlhelpers.find_urls(r))
    
    
    def test_download_image(self):
        # Establish test dir
        output_dir = "test_dir"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Download files as .jpgs
        app.urlhelpers.download_image("https://i.redd.it/qqgds2i3ueh31.jpg", "a", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "a.jpeg")))

        app.urlhelpers.download_image("https://i.redd.it/mfqm1x49akgy.jpg", "b", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "b.jpeg")))

        app.urlhelpers.download_image("https://i.redd.it/jh0gfb3ktvkz.jpg", "c", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "c.jpeg")))

        app.urlhelpers.download_image("https://i.imgur.com/ppqan5G.jpg", "d", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "d.jpeg")))

        app.urlhelpers.download_image("https://i.imgur.com/CS8QhJG.jpg", "e", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "e.jpeg")))

        app.urlhelpers.download_image("https://i.imgur.com/B6HPXkk.jpg", "f", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "f.jpeg")))


        # Download files as .pngs
        app.urlhelpers.download_image("https://i.redd.it/qqgds2i3ueh31.jpg", "a", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "a.png")))

        app.urlhelpers.download_image("https://i.redd.it/mfqm1x49akgy.jpg", "b", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "b.png")))
        
        app.urlhelpers.download_image("https://i.redd.it/jh0gfb3ktvkz.jpg", "c", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "c.png")))
        
        app.urlhelpers.download_image("https://i.imgur.com/ppqan5G.jpg", "d", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "d.png")))
        
        app.urlhelpers.download_image("https://i.imgur.com/CS8QhJG.jpg", "e", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "e.png")))
        
        app.urlhelpers.download_image("https://i.imgur.com/B6HPXkk.jpg", "f", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "f.png")))

        # Remove test directory
        shutil.rmtree(output_dir)
        shutil.rmtree("temp")


if __name__ == '__main__':
    unittest.main()
