from functools import partial

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from alltime11 import validators
from alltime11.models import BaseModel
from users.validators import validate_pincode, validate_state_code
from utils.shortuuid import generate


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, username=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('Phone number must be set'))
        user = self.model(phone_number=phone_number, username=username, password=password, **extra_fields)
        if not username:
            user.username = user.uid
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, phone_number, password=None, **extra_fields):
        extra_fields["is_superuser"] = True
        extra_fields["is_staff"] = True
        extra_fields["is_active"] = True
        return self.create_user(phone_number, username, password, **extra_fields)


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    gender_choices = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    username_validator = UnicodeUsernameValidator()
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    uid = models.CharField(default=partial(generate, prefix='S'), unique=True, max_length=20, db_index=True)
    phone_number = PhoneNumberField(max_length=15, unique=True, null=False, blank=False, db_index=True)
    username = models.CharField(_("username"), max_length=50, unique=True, null=False, blank=False,
                                help_text=_(
                                    "Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only."
                                ),
                                validators=[username_validator],
                                error_messages={"unique": _("A user with that username already exists.")},
                                )
    name = models.CharField(_("name"), max_length=100, blank=False)
    dob = models.DateField(_("dob"), null=True)
    email = models.EmailField(_("email address"), blank=False)
    gender = models.CharField(max_length=1, choices=gender_choices, default='M')
    image_url = models.CharField(max_length=200, null=True)
    address1 = models.CharField(max_length=100, null=True, blank=False)
    address2 = models.CharField(max_length=100, null=True, blank=False)
    city = models.CharField(max_length=30, null=True, blank=False)
    state_code = models.CharField(max_length=5, null=True, blank=False, validators=[validate_state_code])
    pincode = models.CharField(max_length=20, null=True, blank=False, validators=[validate_pincode])
    country = models.CharField(max_length=2, null=True, blank=False, validators=[validators.validate_country_code])
    referral_code = models.CharField(default=partial(generate, prefix='R', max_length=6), unique=True, max_length=6)
    via_referral_code = models.CharField(null=True, max_length=6, blank=False)
    is_email_verified = models.BooleanField(_("email_verified"), default=False, help_text=_(
        "Designates whether the user's email is verified or not"
    ))
    is_staff = models.BooleanField(_("is_staff"), default=False,
                                   help_text=_("Designates the type of user - normal, staff, etc."))
    is_active = models.BooleanField(_("active"), default=True, help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ))
    is_blocked = models.BooleanField(_("blocked"), default=False, help_text=_(
        "Designates whether this user has been debarred from using the platform"
    ))
    avatar_id = models.IntegerField(null=True)
    # firebase tokens
    firebase_token = models.CharField(max_length=250, null=True, help_text=("Firebase user device token"))

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.phone_number:
            raise ValueError("Please provide phone number of the user.")
        if not self.username:
            self.username = self.uid
        super(AbstractBaseUser, self).save(*args, **kwargs)

    def __repr__(self):
        return f"<User - id:{self.pk} - ph:{self.phone_number} - username:{self.username}>"

    def __str__(self):
        return f"<User - id:{self.pk} - ph:{self.phone_number} - username:{self.username}>"
