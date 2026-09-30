"""Norwegian organization-number validation."""

import re


def normalize_org_number(value: str) -> str:
    """Return a nine-digit organization number or raise ``ValueError``."""

    if not isinstance(value, str):
        raise ValueError("organization number must be text")
    digits = re.sub(r"\s+", "", value)
    if not digits.isdigit() or len(digits) != 9:
        raise ValueError("organization number must contain exactly 9 digits")
    return digits


def validate_org_number(value: str) -> bool:
    """Validate the Norwegian MOD-11 check digit."""

    try:
        digits = normalize_org_number(value)
    except ValueError:
        return False
    weights = (3, 2, 7, 6, 5, 4, 3, 2)
    remainder = sum(int(digit) * weight for digit, weight in zip(digits[:8], weights)) % 11
    check_digit = 0 if remainder == 0 else 11 - remainder
    return check_digit != 10 and check_digit == int(digits[-1])
