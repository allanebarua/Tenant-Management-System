import bcrypt
import phonenumbers
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_email
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils import timezone
from rest_framework.authtoken.models import Token

from keja.common.models import KejaBase

# User type options.
LANDLORD = 'LANDLORD'
TENANT = 'TENANT'
ADMIN = 'ADMIN'
USER_TYPES = (
    (LANDLORD, 'LANDLORD'),
    (TENANT, 'TENANT'),
    (ADMIN, 'ADMIN')
)

# Contact type options.
PHONE_CONTACT = 'PHONE'
EMAIL_CONTACT = 'EMAIL'
CONTACT_TYPES = (
    (PHONE_CONTACT, 'PHONE'),
    (EMAIL_CONTACT, 'EMAIL')
)


class KejaUser(KejaBase, AbstractUser):
    """Store for system users."""

    dob = models.DateField(null=True, blank=True)
    national_id_no = models.IntegerField(null=True, blank=True, unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    landlord = models.OneToOneField('KejaUser', null=True, blank=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.user_type in [LANDLORD, ADMIN]:
            self.landlord = None

        self.is_staff = self.user_type == ADMIN
        dt = timezone.now()
        self.created = dt
        self.updated = dt

        # Only set password if creating a new user or when explicitly requested
        # by user update requests.
        if not self.id or kwargs.get('set_password') is True:
            self.set_password(self.password)

        self.full_clean(exclude=None)
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = bcrypt.hashpw(
            self.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self._password = raw_password


class Contact(KejaBase):
    """Store for user contacts."""
    owner = models.ForeignKey(KejaUser, related_name='user_contacts', on_delete=models.CASCADE)
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    contact_value = models.CharField(max_length=256)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        self.validate_phone_number()
        self.validate_email()
        super().clean(*args, **kwargs)

    def validate_phone_number(self):
        if self.contact_type != PHONE_CONTACT:
            return

        try:
            parsed_phone_no = phonenumbers.parse(self.contact_value, 'KE')
            self.contact_value = phonenumbers.format_number(
                parsed_phone_no, phonenumbers.PhoneNumberFormat.E164
            )
        except Exception as exc:
            raise ValidationError({'format_phone_number': str(exc)})

    def validate_email(self):
        if self.contact_type == EMAIL_CONTACT:
            validate_email(self.contact_value)


@receiver(post_save, sender=KejaUser)
def create_auth_token(sender, instance, created=False, **kwargs):
    """Create an authentication token for new users."""
    if created:
        Token.objects.get_or_create(user=instance)
