"""Validation helpers for Norwegian organization numbers."""

import re

from pydantic import AfterValidator
from typing_extensions import Annotated


def validate_org_number(value: str) -> str:
    """Validate and normalize a Norwegian organization number.

    The check digit uses modulo 11 with weights 3, 2, 7, 6, 5, 4, 3, 2.
    """
    digits = re.sub(r"\s+", "", value)
    if not digits.isdigit() or len(digits) != 9:
        raise ValueError("organization number must contain exactly 9 digits")
    checksum = sum(int(digit) * weight for digit, weight in zip(digits[:8], (3, 2, 7, 6, 5, 4, 3, 2)))
    remainder = checksum % 11
    check_digit = 0 if remainder == 0 else 11 - remainder
    if check_digit == 10 or check_digit != int(digits[8]):
        raise ValueError("invalid Norwegian organization number check digit")
    return digits


OrgNumber = Annotated[str, AfterValidator(validate_org_number)]
