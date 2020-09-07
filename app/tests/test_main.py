class TestMainFunctions(unittest.TestCase):

    def test_sign_in(self):
        with self.assertRaises(ConnectionError):
            main.sign_in("", "")


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
