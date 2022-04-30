"""Common Models."""
from django.db import models
from django.utils import timezone


class KejaBase(models.Model):
    """Base class for all models."""

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        """Override save method to restrit updates to created field."""
        if self.pk:
            self.created = self.__class__.objects.get(id=self.pk).created

        super().save(*args, **kwargs)

    class Meta():
        """Meta class."""

        abstract = True
