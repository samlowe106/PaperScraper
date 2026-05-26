import json
import unittest


class TestRedditParser(unittest.IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("tests/parsing/reddit_test_data.json") as f:
            json_data = json.load(f)

        self.single_image_url = json_data["single_image"][0]["url"]
        self.single_image_url = set(json_data["single_image"][0]["expected"])
        self.gallery_url = json_data["gallery"][0]["url"]
        self.gallery_expected = set(json_data["gallery"][0]["expected"])

    def test_single_image(self):
        pass

    def test_gallery(self):
        pass


"""
    submission = clients.reddit.submission(url=url)

    parsed = urlparse(submission.url)

    # single image
    if parsed.netloc == "i.redd.it":
        return {submission.url}

    # gallery post
    if submission.is_gallery:
        items = []
        for item in submission.gallery_data["items"]:
            media_id = item["media_id"]

            metadata = submission.media_metadata[media_id]

            # Get the original image and unescape ampersands
            img_url = metadata["s"]["u"].replace("&amp;", "&")
            items.append(img_url)
        return set(items)

    return set()
"""
