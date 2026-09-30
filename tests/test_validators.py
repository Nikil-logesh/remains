import pytest
from pydantic import BaseModel, ValidationError

from signalpost.validators import OrgNumber, validate_org_number


class Input(BaseModel):
    org_number: OrgNumber


def test_valid_org_number_is_normalized():
    assert validate_org_number(" 984 851 006 ") == "984851006"
    assert Input(org_number="984851006").org_number == "984851006"


@pytest.mark.parametrize("value", ["123", "984851007", "abcdefghi"])
def test_invalid_org_number_is_rejected(value):
    with pytest.raises((ValueError, ValidationError)):
        Input(org_number=value)
