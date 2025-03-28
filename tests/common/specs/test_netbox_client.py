import pytest

from nopf.client import Version


def test_invalid_version():
    with pytest.raises(ValueError):
        Version("invalid")
