"""Viewsets for user and contacts management."""
from django.db.models import Q
from rest_framework import exceptions, status
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from keja.keja_user.filters import ContactFilter, KejaUserFilter
from keja.keja_user.models import LANDLORD, Contact, KejaUser
from keja.keja_user.serializers import ContactSerializer, KejaUserSerializer


class KejaUserViewSet(ModelViewSet):
    """User management Viewset."""

    queryset = KejaUser.objects.all()
    serializer_class = KejaUserSerializer
    filter_class = KejaUserFilter

    def list(self, request, *args, **kwargs):
        """List system users."""
        queryset = self.get_queryset()

        if request.user.is_staff:
            pass

        elif request.user.user_type == LANDLORD:
            queryset = queryset.filter(
                Q(landlord=request.user) | Q(id=request.user.id))

        else:
            queryset = KejaUser.objects.filter(id=request.user.id)

        serialized_users = self.serializer_class(queryset, many=True)
        return Response(serialized_users.data)

    def update(self, request, *args, **kwargs):
        """Update an existing database object.

        Can be used for both update and partial updates.
        """
        user = self.get_object()
        if not request.user.is_staff and user != request.user:
            raise exceptions.PermissionDenied(
                f'user {request.user.id} cannot update user {user.id}')

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a user."""
        if not request.user.is_staff:
            raise exceptions.PermissionDenied()

        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """Override creation of users to explicitly pass the creator."""
        serializer.save(owner=self.request.user)

    def check_object_permissions(self, request, obj):
        """Check Whether the user is allowed to access the database object."""
        permitted = (
            request.user.is_staff
            or request.user == obj
            or request.user == obj.landlord
        )

        if not permitted:
            raise exceptions.PermissionDenied(
                f'user {request.user.id} cannot retrive user {obj.id}')

    def get_queryset(self):
        """Get filtered queryset."""
        return self.filter_queryset(super().get_queryset())


class ContactViewSet(
        RetrieveModelMixin,
        ListModelMixin,
        CreateModelMixin,
        UpdateModelMixin,
        GenericViewSet):
    """User management Viewset."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_class = ContactFilter

    def list(self, request, *args, **kwargs):
        """Return a list of contacts."""
        queryset = self.get_queryset()

        extras = Q(user__id=kwargs['pk']) if kwargs.get('pk') else Q()

        if request.user.is_staff is True:
            queryset = queryset.filter(extras)

        elif request.user.user_type == LANDLORD:
            queryset = queryset.filter(
                extras, Q(owner=request.user) | Q(owner__landlord=request.user))

        else:
            queryset = queryset.filter(extras, owner=request.user)

        serialized_contacts = ContactSerializer(queryset, many=True)
        return Response(serialized_contacts.data)

    def update(self, request, *args, **kwargs):
        """Update a contact."""
        contact = self.get_object()
        partial = kwargs.pop('partial', False)
        validated_data = self.serializer_class(
            contact, data=request.data, partial=partial)
        validated_data.is_valid(raise_exception=True)
        validated_data.save()
        return Response(validated_data.data)

    def perform_create(self, serializer):
        """Create a contact."""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Get filtered queryset."""
        return self.filter_queryset(super().get_queryset())

    def check_object_permissions(self, request, obj):
        """Check Whether the user is allowed to access the database object."""
        permitted = (
            request.user.is_staff
            or request.user == obj.owner
        )

        if not permitted:
            raise exceptions.PermissionDenied()
