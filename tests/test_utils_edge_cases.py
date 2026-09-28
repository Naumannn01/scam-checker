import pytest

from app.utils import classify_input


@pytest.mark.parametrize("value", ["", "   ", "hello world", "just some words", "http://", "@ybl"])
def test_rejects_garbage_input(value):
    assert classify_input(value) is None


def test_phone_number_as_upi_handle_is_upi():
    assert classify_input("9876543210@ybl") == "upi"


def test_uppercase_upi_handle_is_upi():
    assert classify_input("Scammer@YBL") == "upi"


def test_url_with_path_and_query_is_url():
    assert classify_input("https://example.com/login?next=/pay") == "url"


def test_surrounding_whitespace_is_ignored():
    assert classify_input("  google.com  ") == "url"


def test_ten_digits_starting_below_six_is_not_a_phone():
    assert classify_input("1234567890") is None

def test_internationalized_domain_is_url():
    assert classify_input("bücher.de") == "url"


def test_raw_ip_url_is_url():
    assert classify_input("http://192.168.1.1/login") == "url"