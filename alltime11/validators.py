from django.core.validators import ValidationError

from . import constants as C


def validate_country_code(value):
    valid_country_codes = set(C.alpha_2_country_codes.keys())

    if value not in valid_country_codes:
        raise ValidationError(f"'{value} not a valid 2 letter country code")


def validate_contest_creator(value):
    if not any([value.is_staff, value.is_superuser]):
        raise ValidationError("Only staff/superuser can create contests")


def validate_batsman_count(value):
    if value < C.MIN_BAT_COUNT:
        raise ValidationError(f"Bastman count should be more than: {C.MIN_BAT_COUNT}")


def validate_bowler_count(value):
    if value < C.MIN_BOW_COUNT:
        raise ValidationError(f"Bowler count should be more than: {C.MIN_BOW_COUNT}")


def validate_all_rounder_count(value):
    if value < C.MIN_ALL_R_COUNT:
        raise ValidationError(f"all rounder count should be more than: {C.MIN_ALL_R_COUNT}")


def validate_keeper_count(value):
    if value < C.MIN_ALL_R_COUNT:
        raise ValidationError(f"keeper count should be more than: {C.MIN_KEEPER_COUNT}")

def validate_slider_creator(value):
    if not any([value.is_staff, value.is_superuser]):
        raise ValidationError("Only staff/superuser can create sliders")