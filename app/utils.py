import re

UPI_REGEX = re.compile(r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$")
PHONE_REGEX = re.compile(r"^(\+91)?[6-9]\d{9}$")

def classify_input(value: str) -> str:
    value = value.strip()

    if value.startswith("http://") or value.startswith("https://") or "." in value and " " not in value and "@" not in value:
        # crude first pass — refine in Step 3 with proper URL validation
        if UPI_REGEX.match(value):
            return "upi"
        return "url"

    if UPI_REGEX.match(value):
        return "upi"

    if PHONE_REGEX.match(value.replace(" ", "").replace("-", "")):
        return "phone"

    return "url"  # fallback, we'll tighten this later