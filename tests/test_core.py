from core import file_title


def test_remove_invalid():
    pass


def test_reduce_whitespace():
    pass


def test_file_title():
    assert file_title("mock title") == "mock title"
    assert file_title("mock title: \\") == "mock title"
    assert file_title("mock title: ??") == "mock title"
    assert file_title("mock ?? title: \\") == "mock title"
