
""" Unless otherwise stated, NONE of the URLs used for testing should be dead. """


class TestURLHelpers(unittest.TestCase):
    

    def test_recognized(self):
        self.assertTrue(helpers.urlhelpers.recognized(".png"))
        self.assertTrue(helpers.urlhelpers.recognized(".PnG"))
        self.assertTrue(helpers.urlhelpers.recognized(".PNG"))
        self.assertTrue(helpers.urlhelpers.recognized(".jpg"))
        self.assertTrue(helpers.urlhelpers.recognized(".jpeg"))
        self.assertTrue(helpers.urlhelpers.recognized(".gif"))

        self.assertFalse(helpers.urlhelpers.recognized("bar"))
        self.assertFalse(helpers.urlhelpers.recognized(".foo"))
        self.assertFalse(helpers.urlhelpers.recognized("arbitrary"))
        self.assertFalse(helpers.urlhelpers.recognized("gif"))
        self.assertFalse(helpers.urlhelpers.recognized("png"))
        self.assertFalse(helpers.urlhelpers.recognized("file.png"))


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
                          helpers.urlhelpers.parse_imgur_album("https://imgur.com/a/rSZlZ"))
        
        self.assertEqual(["https://i.imgur.com/oPXMrnr.png",
                          "https://i.imgur.com/Au8PAtj.png"],
                          helpers.urlhelpers.parse_imgur_album("https://imgur.com/gallery/NXBcU"))
        
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
                          helpers.urlhelpers.parse_imgur_album("https://imgur.com/a/uZJHE"))
        

    def test_parse_imgur_single(self):
        self.assertEqual("https://i.imgur.com/jTAD7G1.jpg",
                         helpers.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/jTAD7G1"))
        self.assertEqual("https://i.imgur.com/WVntmOE.jpg",
                         helpers.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/WVntmOE"))
        self.assertEqual("https://i.imgur.com/rzOOFgI.jpg",
                         helpers.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/rzOOFgI"))
        self.assertEqual("https://i.imgur.com/mtjTo2o.jpg",
                         helpers.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/mtjTo2o"))
        self.assertEqual("https://i.imgur.com/mgfgDYb.jpg",
                         helpers.urlhelpers.parse_imgur_single("https://imgur.com/r/Wallpapers/mgfgDYb"))


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
                self.assertEqual(extension, helpers.urlhelpers.get_extension(r))


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
                self.assertEqual(expected, helpers.urlhelpers.find_urls(r))
    
    
    def test_download_image(self):
        # Establish test dir
        output_dir = "test_dir"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Download files as .jpgs
        helpers.urlhelpers.download_image("https://i.redd.it/qqgds2i3ueh31.jpg", "a", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "a.jpeg")))

        helpers.urlhelpers.download_image("https://i.redd.it/mfqm1x49akgy.jpg", "b", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "b.jpeg")))

        helpers.urlhelpers.download_image("https://i.redd.it/jh0gfb3ktvkz.jpg", "c", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "c.jpeg")))

        helpers.urlhelpers.download_image("https://i.imgur.com/ppqan5G.jpg", "d", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "d.jpeg")))

        helpers.urlhelpers.download_image("https://i.imgur.com/CS8QhJG.jpg", "e", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "e.jpeg")))

        helpers.urlhelpers.download_image("https://i.imgur.com/B6HPXkk.jpg", "f", output_dir, png=False)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "f.jpeg")))


        # Download files as .pngs
        helpers.urlhelpers.download_image("https://i.redd.it/qqgds2i3ueh31.jpg", "a", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "a.png")))

        helpers.urlhelpers.download_image("https://i.redd.it/mfqm1x49akgy.jpg", "b", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "b.png")))
        
        helpers.urlhelpers.download_image("https://i.redd.it/jh0gfb3ktvkz.jpg", "c", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "c.png")))
        
        helpers.urlhelpers.download_image("https://i.imgur.com/ppqan5G.jpg", "d", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "d.png")))
        
        helpers.urlhelpers.download_image("https://i.imgur.com/CS8QhJG.jpg", "e", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "e.png")))
        
        helpers.urlhelpers.download_image("https://i.imgur.com/B6HPXkk.jpg", "f", output_dir, png=True)
        self.assertTrue(os.path.isfile(os.path.join(output_dir, "f.png")))
