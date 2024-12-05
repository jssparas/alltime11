from django.core.exceptions import ValidationError

from alltime11 import constants


def validate_pincode(value):
    # TODO: this validation is specific to INDIA only, adapt for other countries in future
    if not value.isdigit() or len(value) != 6:
        raise ValidationError("Invalid pincode. It must be a 6-digit number.")


def validate_state_code(value):
    # TODO: state_code_to_name is specific to INDIA only, add for other countries in future
    valid_state_codes = set(constants.state_code_to_name.keys())

    if value not in valid_state_codes:
        raise ValidationError(f"'{value}' is not a valid state code.")
