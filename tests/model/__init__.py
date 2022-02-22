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