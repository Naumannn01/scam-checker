import ipaddress
import re
from typing import Optional
from urllib.parse import urlparse

UPI_REGEX = re.compile(r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$")
PHONE_REGEX = re.compile(r"^(\+91)?[6-9]\d{9}$")
DOMAIN_REGEX = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+"
    r"(?:[a-z]{2,63}|xn--[a-z0-9\-]{1,59})$",
    re.IGNORECASE,
)


def _is_valid_host(host: Optional[str]) -> bool:
    if not host:
        return False
    host = host.rstrip(".")

    # raw IPs are common in phishing links, so accept them
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    # convert non-ASCII (lookalike/IDN) domains to punycode so they can be checked
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return bool(DOMAIN_REGEX.match(host))


def classify_input(value: str) -> Optional[str]:
    """Return "url", "upi" or "phone", or None if the input is none of them."""
    value = (value or "").strip()
    if not value:
        return None

    if UPI_REGEX.match(value):
        return "upi"

    if PHONE_REGEX.match(value.replace(" ", "").replace("-", "")):
        return "phone"

    candidate = value if "://" in value else "http://" + value
    try:
        host = urlparse(candidate).hostname
    except ValueError:
        return None

    return "url" if _is_valid_host(host) else None