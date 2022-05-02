"""Serializers for users and their contacts."""
from django.core.validators import validate_email
from rest_framework import serializers

from keja.keja_user.models import (
    ADMIN, EMAIL_CONTACT, LANDLORD, PHONE_CONTACT, TENANT,
    Contact, KejaUser)


class ContactSerializer(serializers.ModelSerializer):
    """Contacts serializer class."""

    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        """Meta class."""

        model = Contact
        fields = ('owner', 'contact_type', 'contact_value', 'is_active')

    def create(self, validated_data):
        """Create new contact from deserialized data."""
        return Contact.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update existing contact using deserialized data."""
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance

    def validate(self, data):
        """Validate contact object."""
        if data.get('contact_type') == PHONE_CONTACT:
            data['contact_value'] = Contact.validate_phone_contact(
                data['contact_value'])

        if data.get('contact_type') == EMAIL_CONTACT:
            validate_email(data['contact_value'])

        return data


class KejaUserSerializer(serializers.ModelSerializer):
    """KejaUser serializer class."""

    user_contacts = ContactSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True)
    created = serializers.DateTimeField(read_only=True, format='%Y-%m-%d')
    landlord = serializers.SlugRelatedField(
        slug_field='username', read_only=True, allow_null=True)

    class Meta:
        """Meta class."""

        model = KejaUser

        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 'is_active',
            'user_type', 'landlord', 'created', 'password', 'user_contacts')

    def create(self, validated_data):
        """Create a new system user."""
        owner = validated_data.pop('owner')

        self._validate_landlord_can_only_create_tenant_users(
            owner, validated_data['user_type'])
        self._validate_admin_cannot_create_tenant_users(
            owner, validated_data['user_type'])
        validated_data['landlord'] = (
            owner if validated_data['user_type'] == TENANT
            else None
        )

        return KejaUser.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing user."""
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance

    def validate(self, data):
        """Perform Object-Level validations."""
        self._validate_landlord_has_email(data)
        return data

    def _validate_landlord_has_email(self, data):
        """Validate that a landlord has an email address."""
        if data.get('user_type') == LANDLORD and not data.get('email'):
            raise serializers.ValidationError({
                'email': 'A Landlord should have an email address.'})

    def _validate_landlord_can_only_create_tenant_users(self, owner, create_user_type):
        """Validate that a landlord can only create tenant accounts."""
        if owner.user_type == LANDLORD and create_user_type != TENANT:
            raise serializers.ValidationError({
                'non_field_errors': 'A Landlord can only create tenant user accounts.'})

    def _validate_admin_cannot_create_tenant_users(self, owner, create_user_type):
        """Validate that an admin cannot create tenant accounts."""
        if owner.user_type == ADMIN and create_user_type == TENANT:
            raise serializers.ValidationError({
                'non_field_errors': 'An Admin cannot create tenant user accounts.'})
