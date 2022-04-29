import stat
from django.db.models import Q
from rest_framework import exceptions, permissions, status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes)
from rest_framework.response import Response

from keja_user.authentication import KejaPasswordAuthentication
from keja_user.filters import ContactFilter, KejaUserFilter
from keja_user.models import LANDLORD, Contact, KejaUser
from keja_user.serializers import ContactSerializer, KejaUserSerializer
from keja_user.utils import get_db_object
from rest_framework import status


def get_queryset(request, manager, filter_class):
    """Filter the default queryset using the `filter_class`"""
    kwargs = {
        'data': request.query_params,
        'request': request,
        'queryset': manager.all()
    }
    filterset = filter_class(**kwargs)

    if not filterset.is_valid():
        raise exceptions.APIException(
            filterset.errors, code=status.HTTP_400_BAD_REQUEST)

    return filterset.qs


@api_view(['GET'])
@authentication_classes([KejaPasswordAuthentication])
@permission_classes([permissions.IsAuthenticated])
def list_keja_users(request, pk=None):
    queryset = get_queryset(request, KejaUser.objects, KejaUserFilter)
    extras = Q(id=pk) if pk else Q()

    if request.user.is_staff:
        queryset = queryset.filter(extras)
    elif request.user.user_type == LANDLORD:
        queryset = queryset.filter(
            extras, Q(landlord=request.user) | Q(id=request.user.id))
    else:
        queryset = queryset.filter(extras, id=request.user.id)

    serialized_users = KejaUserSerializer(queryset, many=True)
    return Response(serialized_users.data)


@api_view(['POST', 'GET'])
@authentication_classes([KejaPasswordAuthentication])
@permission_classes([permissions.IsAuthenticated])
def create_keja_user(request):
    """Create a user."""
    serializer_data = KejaUserSerializer(data=request.data, context={'request': request})
    serializer_data.is_valid(raise_exception=True)
    serializer_data.save(owner=request.user)
    return Response(serializer_data.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@authentication_classes([KejaPasswordAuthentication])
@permission_classes([permissions.IsAuthenticated])
def update_keja_user(request):
    """Update a single user."""
    user = get_db_object(KejaUser, request.data['id'])
    # Non-Admin users can only update themselves.
    if not request.user.is_staff and user != request.user:
        raise exceptions.PermissionDenied(
            f'user {request.user.id} cannot update user {user.id}')

    serialized_data = KejaUserSerializer(user, data=request.data, partial=True)
    serialized_data.is_valid(raise_exception=True)
    serialized_data.save()
    return Response(serialized_data.data)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def delete_keja_user(request, pk):
    """Delete a user instance.

    Utilizes the default authentication policies in the settings.py file.
    """
    user = get_db_object(KejaUser, pk)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_user_contacts(request, pk=None):
    queryset = get_queryset(request, Contact.objects, ContactFilter)
    extras = Q(user__id=pk) if pk else Q()
    # An admin can get all contacts
    if request.user.is_staff is True:
        queryset = queryset.filter(extras)

    # Landlords can get their contacts + contacts for their tenants
    elif request.user.user_type == LANDLORD:
        queryset = queryset.filter(
            extras, Q(owner=request.user) | Q(owner=request.user.landlord))

    # Tenants can get their own contacts.
    else:
        queryset = queryset.filter(extras, owner=request.user)

    serialized_contacts = ContactSerializer(queryset, many=True)
    return Response(serialized_contacts.data)


@api_view(['POST'])
def create_user_contact(request):
    """Create user contact."""
    validated_data = ContactSerializer(data=request.data)
    validated_data.is_valid(raise_exception=True)
    validated_data.save(owner=request.user)
    return Response(validated_data.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
def update_user_contact(request):
    contact = get_db_object(Contact, request.data['id'])
    if contact.user != request.user:
        raise exceptions.PermissionDenied(
            f'User {request.user.id} cannot update contact {contact.id}')

    validated_data = ContactSerializer(data=request.data, partial=True)
    validated_data.is_valid(raise_exception=True)
    validated_data.save()
    return Response(validated_data.data)
