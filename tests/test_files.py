from src.utils import files
import os
import shutil

def sandbox(function, test_dir: str = "test_dir"):
    """
    Executes function in test_dir (making that directory if it doesn't already exist)
    then deletes test_dir
    """
    def makedirs(*args, **kwargs):
        # Establish test dir
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        os.chdir(test_dir)
        
        # Execute the function
        result = function(*args, **kwargs)

        # Remove test_dir
        os.chdir("..")
        shutil.rmtree(test_dir)

        return result
    return makedirs

@sandbox
def test_create_directory(self):

    files.create_directory("directory1")
    self.assertTrue("directory1" in os.listdir(os.getcwd()))

    # Creating a second directory with the same name shouldn't do anything
    files.create_directory("directory1")
    self.assertTrue("directory1" in os.listdir(os.getcwd()))

    files.create_directory("directory2")
    self.assertTrue("directory2" in os.listdir(os.getcwd()))


@sandbox
def test_prevent_collisions(self):

    open("myfile.txt", 'a').close()
    self.assertEqual(os.path.join(os.getcwd, "myfile (1).txt"),
                     files.prevent_collisions("myfile", ".txt", os.getcwd()))

    open("myfile (1).txt", 'a').close()
    self.assertEqual(os.path.join(os.getcwd, "myfile (2).txt"),
                     files.prevent_collisions("myfile", ".txt", os.getcwd()))

    open("f" 'a').close()
    self.assertEqual(os.path.join(os.getcwd, "f (1)"),
                     files.prevent_collisions("f", "", os.getcwd()))

    open("UPPER", 'a').close()
    self.assertEqual(os.path.join(os.getcwd, "f (1)"),
                     files.prevent_collisions("UPPER", "", os.getcwd()))

    open(".fileext", 'a').close()
    self.assertEqual(os.path.join(os.getcwd, " (1).fileext"),
                     files.prevent_collisions("", ".fileext", os.getcwd()))


"""
def test_convert_file(self):
    self.assertEqual(True, False)
"""

def test_remove_invalid(self):
    self.assertEqual("", files.remove_invalid(""))
    self.assertEqual("", files.remove_invalid("\\"))
    self.assertEqual("", files.remove_invalid("/"))
    self.assertEqual("", files.remove_invalid(":"))
    self.assertEqual("", files.remove_invalid("*"))
    self.assertEqual("", files.remove_invalid("?"))
    self.assertEqual("", files.remove_invalid("<"))
    self.assertEqual("", files.remove_invalid(">"))
    self.assertEqual("", files.remove_invalid("|"))
    self.assertEqual("'", files.remove_invalid('"'))
    self.assertEqual("'", files.remove_invalid("'"))
    self.assertEqual("valid filename", files.remove_invalid("valid filename"))
    self.assertEqual("invalid flename", files.remove_invalid("invalid? f|lename"))