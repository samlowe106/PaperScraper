from src.model import urls
import unittest

""" Unless otherwise stated, none of the URLs used for testing should be dead. """


class TestURLS(unittest.TestCase):


    def test_determine_name(self):
        pass


    def test_download(self):
        pass


    def test_get_extension(self):
        pass


    def test_sandbox(self):
        pass

"""
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
            self.assertEqual(extension, urls.get_extension(r))


@sandbox(output_dir := "test_dir")
def test_download_image(self):
    
    # Download files as .jpgs
    urls.download_image("https://i.redd.it/qqgds2i3ueh31.jpg", "a", output_dir, png=False)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "a.jpeg")))

    urls.download_image("https://i.redd.it/mfqm1x49akgy.jpg", "b", output_dir, png=False)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "b.jpeg")))

    urls.download_image("https://i.redd.it/jh0gfb3ktvkz.jpg", "c", output_dir, png=False)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "c.jpeg")))

    urls.download_image("https://i.imgur.com/ppqan5G.jpg", "d", output_dir, png=False)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "d.jpeg")))

    urls.download_image("https://i.imgur.com/CS8QhJG.jpg", "e", output_dir, png=False)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "e.jpeg")))

    urls.download_image("https://i.imgur.com/B6HPXkk.jpg", "f", output_dir, png=False)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "f.jpeg")))


    # Download files as .pngs
    urls.download_image("https://i.redd.it/qqgds2i3ueh31.jpg", "a", output_dir, png=True)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "a.png")))

    urls.download_image("https://i.redd.it/mfqm1x49akgy.jpg", "b", output_dir, png=True)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "b.png")))
    
    urls.download_image("https://i.redd.it/jh0gfb3ktvkz.jpg", "c", output_dir, png=True)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "c.png")))
    
    urls.download_image("https://i.imgur.com/ppqan5G.jpg", "d", output_dir, png=True)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "d.png")))
    
    urls.download_image("https://i.imgur.com/CS8QhJG.jpg", "e", output_dir, png=True)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "e.png")))
    
    urls.download_image("https://i.imgur.com/B6HPXkk.jpg", "f", output_dir, png=True)
    self.assertTrue(os.path.isfile(os.path.join(output_dir, "f.png")))
"""