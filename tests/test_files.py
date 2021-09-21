"""
import os


@files.sandbox("test_dir")
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


def test_convert_file(self):
    self.assertEqual(True, False)


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
    
"""