TEST_DIR_NAME = "test_dir"

def mk_testdir():
    # Establish test dir
    if not os.path.exists(TEST_DIR_NAME):
        os.makedirs(TEST_DIR_NAME)
    os.chdir(TEST_DIR_NAME)
    return


def rm_testdir():
    # Remove test directory
    os.chdir("..")
    shutil.rmtree(TEST_DIR_NAME)
    return










# Remove test directory
shutil.rmtree(output_dir)
shutil.rmtree("temp")
