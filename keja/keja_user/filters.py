"""Django-Filters for users and contacts."""
from django_filters import rest_framework as filters

from keja.keja_user.models import Contact, KejaUser


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """Filter class to validate comma separated list of strings.

    The BaseInFilter validates that the input is comma-separated
    The CharFilter validates the individual values to be characters
    """

    pass


class KejaUserFilter(filters.FilterSet):
    """KejaUser Filter class."""

    user_type = filters.CharFilter(field_name='user_type', lookup_expr='exact')
    landlord = filters.CharFilter(field_name='landlord__username', lookup_expr='exact')
    username = filters.CharFilter(field_name='username', lookup_expr='iexact')

    class Meta:
        """Meta class for user filters."""

        model = KejaUser
        fields = ['is_active']


class ContactFilter(filters.FilterSet):
    """Contact Filter class."""

    contact_type__in = CharInFilter(field_name='contact_type', lookup_expr='in')

    class Meta:
        """Meta class for contact filters."""

        model = Contact
        fields = ['contact_type', 'is_active', 'contact_value']
