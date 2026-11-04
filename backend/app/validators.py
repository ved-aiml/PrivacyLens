import ipaddress
import re
import uuid


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

    return len(digits) == 10 and digits[0] in "6789"


def validate_pincode(value: str) -> bool:
    return bool(re.fullmatch(r"[1-9]\d{5}", value))


def validate_pan(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", value, re.IGNORECASE))


def validate_aadhaar_format(value: str) -> bool:
    digits = re.sub(r"[\s-]", "", value)
    return (
        len(digits) == 12
        and digits.isdigit()
        and digits[0] not in ("0", "1")
    )


def validate_ifsc(value: str) -> bool:
    clean = value.strip().upper()
    return bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", clean))


def validate_upi(value: str) -> bool:
    clean = value.strip()
    if "@" not in clean:
        return False
    # Exclude common standard email domains to avoid conflict with EMAIL
    domain = clean.split("@")[-1].lower()
    common_email_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"}
    return domain not in common_email_domains


def validate_gstin(value: str) -> bool:
    clean = value.strip().upper()
    if len(clean) != 15:
        return False
    pan_part = clean[2:12]
    return validate_pan(pan_part)


def validate_voter_id(value: str) -> bool:
    clean = value.strip().upper()
    return bool(re.fullmatch(r"[A-Z]{3}[0-9]{7}", clean))


def validate_passport(value: str) -> bool:
    clean = value.strip().upper()
    return bool(re.fullmatch(r"[A-PR-WYa-pr-wy][1-9]\d{6}", clean))


def validate_uuid(value: str) -> bool:
    try:
        uuid.UUID(value.strip())
        return True
    except (ValueError, AttributeError):
        return False


def validate_mac(value: str) -> bool:
    clean = value.strip()
    return bool(re.fullmatch(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", clean))



def validate_ifsc(value: str) -> bool:
    clean = value.strip().upper()
    return bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", clean))


def validate_upi(value: str) -> bool:
    clean = value.strip()
    if "@" not in clean:
        return False
    # Exclude common standard email domains to avoid conflict with EMAIL
    domain = clean.split("@")[-1].lower()
    common_email_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"}
    return domain not in common_email_domains


def validate_gstin(value: str) -> bool:
    clean = value.strip().upper()
    if len(clean) != 15:
        return False
    pan_part = clean[2:12]
    return validate_pan(pan_part)


def validate_voter_id(value: str) -> bool:
    clean = value.strip().upper()
    return bool(re.fullmatch(r"[A-Z]{3}[0-9]{7}", clean))


def validate_passport(value: str) -> bool:
    clean = value.strip().upper()
    return bool(re.fullmatch(r"[A-PR-WYa-pr-wy][1-9]\d{6}", clean))


def validate_uuid(value: str) -> bool:
    try:
        uuid.UUID(value.strip())
        return True
    except (ValueError, AttributeError):
        return False


def validate_mac(value: str) -> bool:
    clean = value.strip()
    return bool(re.fullmatch(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", clean))