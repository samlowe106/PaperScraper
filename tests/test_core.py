from core import file_title


def test_file_title():
    assert file_title("mock title") == "mock title"
    assert file_title("mock title: \\") == "mock title"
    assert file_title("mock title: ??") == "mock title"
    assert file_title("mock ?? title: \\") == "mock title"
