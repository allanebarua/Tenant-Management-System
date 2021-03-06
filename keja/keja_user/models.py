"""Models for users and contacts."""
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
    landlord = models.OneToOneField(
        'KejaUser', null=True, blank=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        """Save KejaUser instances."""
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
        """Hash user password."""
        self.password = bcrypt.hashpw(
            self.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self._password = raw_password


class Contact(KejaBase):
    """Store for user contacts."""

    owner = models.ForeignKey(
        KejaUser, related_name='user_contacts', on_delete=models.CASCADE)
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    contact_value = models.CharField(max_length=256)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Save Contact instances."""
        self.clean()
        super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """Validate contact fields."""
        self._validate_phone_number()
        self.validate_email()
        super().clean(*args, **kwargs)

    def _validate_phone_number(self):
        """Validate phone numbers."""
        if self.contact_type == PHONE_CONTACT:
            self.contact_value = Contact.validate_phone_contact(
                self.contact_value)

    def validate_email(self):
        """Validate email contacts."""
        if self.contact_type == EMAIL_CONTACT:
            validate_email(self.contact_value)

    @classmethod
    def validate_phone_contact(cls, phone_number):
        """Validate phone contact."""
        try:
            parsed_phone_no = phonenumbers.parse(phone_number, 'KE')
            return phonenumbers.format_number(
                parsed_phone_no, phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            raise ValidationError('Invalid phone number supplied.')


@receiver(post_save, sender=KejaUser)
def create_auth_token(sender, instance, created=False, **kwargs):
    """Create an authentication token for new users."""
    if created:
        Token.objects.get_or_create(user=instance)
