from app.utils import classify_input


def test_classifies_upi_id():
    assert classify_input("scammer@ybl") == "upi"


def test_classifies_plain_phone_number():
    assert classify_input("9876543210") == "phone"


def test_classifies_phone_with_country_code():
    assert classify_input("+919876543210") == "phone"


def test_classifies_phone_with_spaces_and_dashes():
    assert classify_input("98765-43210") == "phone"


def test_classifies_bare_domain_as_url():
    assert classify_input("google.com") == "url"


def test_classifies_full_url():
    assert classify_input("http://paytm-refund-verify.tk") == "url"