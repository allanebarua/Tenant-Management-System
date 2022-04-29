from django.db import models
from django.utils import timezone


class KejaBase(models.Model):
    """Base class for all models."""

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Prevent change of created when updating a record.
        if self.pk:
            self.created = self.__class__.objects.get(id=self.pk).created

        super().save(*args, **kwargs)


    class Meta():
        abstract = True
