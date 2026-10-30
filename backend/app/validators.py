import ipaddress
import re


def validate_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def validate_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)

    # Remove Indian country code or leading zero.
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    return (
        len(digits) == 10
        and digits[0] in "6789"
    )


def validate_pincode(value: str) -> bool:
    return (
        bool(re.fullmatch(r"[1-9]\d{5}", value))
    )