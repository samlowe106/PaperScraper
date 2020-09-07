import helpers.files


class Testfiles(unittest.TestCase):
    

    def test_create_directory(self):
        mk_testdir() # lol

        helpers.files.create_directory("directory1")
        self.assertTrue("directory1" in os.listdir(os.getcwd()))

        # Creating a second directory with the same name shouldn't do anything
        helpers.files.create_directory("directory1")
        self.assertTrue("directory1" in os.listdir(os.getcwd()))

        helpers.files.create_directory("directory2")
        self.assertTrue("directory2" in os.listdir(os.getcwd()))

        rm_testdir()


    def test_prevent_collisions(self):
        mk_testdir()

        open("myfile.txt", 'a').close()
        self.assertEqual(os.path.join(os.getcwd, "myfile (1).txt"),
                                      helpers.files.prevent_collisions("myfile", ".txt", os.getcwd()))

        open("myfile (1).txt", 'a').close()
        self.assertEqual(os.path.join(os.getcwd, "myfile (2).txt"),
                         helpers.files.prevent_collisions("myfile", ".txt", os.getcwd()))

        open("f" 'a').close()
        self.assertEqual(os.path.join(os.getcwd, "f (1)"),
                         helpers.files.prevent_collisions("f", "", os.getcwd()))

        open("UPPER", 'a').close()
        self.assertEqual(os.path.join(os.getcwd, "f (1)"),
                                      helpers.files.prevent_collisions("UPPER", "", os.getcwd()))
    
        open(".fileext", 'a').close()
        self.assertEqual(os.path.join(os.getcwd, " (1).fileext"),
                                      helpers.files.prevent_collisions("", ".fileext", os.getcwd()))

        rm_testdir()


    """
    def test_convert_file(self):
        self.assertEqual(True, False)
    """