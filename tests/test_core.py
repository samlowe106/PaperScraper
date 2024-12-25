import httpx
import pytest

from core import get_extension, retitle  # determine_name,


class TestGetExtension:
    """Actually makes get requests!"""

    @pytest.mark.vcr
    def test_jpeg(self):
        # Mushroom Generator by beeple
        r = httpx.get(
            "https://cdna.artstation.com/p/assets/images/images/012/127/414/large/beeple-07-25-18.jpg?1533161904"
        )
        assert get_extension(r) == ".jpeg"

    @pytest.mark.vcr
    def test_png(self):
        # Early Summer Holiday by 六七質
        r = httpx.get("https://i.redd.it/1u3xx7t7tmra1.png")
        assert get_extension(r) == ".png"


def test_retitle():
    assert retitle("mock title") == "mock title"
    assert retitle("mock title: \\") == "mock title"
    assert retitle("mock title: ??") == "mock title"
    assert retitle("mock ?? title: \\") == "mock title"
