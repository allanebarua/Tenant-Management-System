from django.db.models import Q
from rest_framework import exceptions, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from keja_user.authentication import (
    KejaPasswordAuthentication, KejaTokenAuthentication)
from keja_user.filters import ContactFilter, KejaUserFilter
from keja_user.models import LANDLORD, Contact, KejaUser
from keja_user.serializers import ContactSerializer, KejaUserSerializer
from keja_user.utils import get_db_object


class KejaAPIView(APIView):
    """Allow custom filtering of objects using django-filters."""

    def get_queryset(self, request):
        kwargs = {
            'data': request.query_params,
            'request': request,
            'queryset': self.queryset
        }
        filterset = self.filter_class(**kwargs)

        if not filterset.is_valid():
            raise exceptions.APIException(
                filterset.errors, code=status.HTTP_400_BAD_REQUEST)

        return filterset.qs


class KejaUserView(KejaAPIView):
    """Class view for user management."""

    authentication_classes = [KejaTokenAuthentication, KejaPasswordAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = KejaUser.objects.all()
    filter_class = KejaUserFilter

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)

        extras = Q(id=kwargs['pk']) if kwargs.get('pk') else Q()
        if request.user.is_staff:
            queryset = queryset.filter(extras)
        elif request.user.user_type == LANDLORD:
            queryset = queryset.filter(
                extras, Q(landlord=request.user) | Q(id=request.user.id))
        else:
            queryset = queryset.filter(extras, id=request.user.id)

        serialized_users = KejaUserSerializer(queryset, many=True)
        return Response(serialized_users.data)

    def post(self, request, *args, **kwargs):
        serializer_data = KejaUserSerializer(data=request.data, context={'request': request})
        serializer_data.is_valid(raise_exception=True)
        serializer_data.save(owner=request.user)
        return Response(serializer_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        user = get_db_object(KejaUser, request.data['id'])
        if not request.user.is_staff and user != request.user:
            raise exceptions.PermissionDenied(
                f'user {request.user.id} cannot update user {user.id}')

        serialized_data = KejaUserSerializer(user, data=request.data, partial=True)
        serialized_data.is_valid(raise_exception=True)
        serialized_data.save()
        return Response(serialized_data.data)

    def delete(self, request, *args, **kwargs):
        user = get_db_object(KejaUser, kwargs['pk'])
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContactView(KejaAPIView):
    """Class based view for contacts management."""
    queryset = Contact.objects.all()
    filter_class = ContactFilter

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)

        extras = Q(user__id=kwargs['pk']) if kwargs.get('pk') else Q()

        if request.user.is_staff is True:
            queryset = queryset.filter(extras)

        elif request.user.user_type == LANDLORD:
            queryset = queryset.filter(
                extras, Q(owner=request.user) | Q(owner=request.user.landlord))

        else:
            queryset = queryset.filter(extras, owner=request.user)

        serialized_contacts = ContactSerializer(queryset, many=True)
        return Response(serialized_contacts.data)

    def post(self, request, *args, **kwargs):
        validated_data = ContactSerializer(data=request.data)
        validated_data.is_valid(raise_exception=True)
        validated_data.save(owner=request.user)
        return Response(validated_data.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        contact = get_db_object(Contact, request.data['id'])
        if contact.user != request.user:
            raise exceptions.PermissionDenied(
                f'User {request.user.id} cannot update contact {contact.id}')

        validated_data = ContactSerializer(data=request.data, partial=True)
        validated_data.is_valid(raise_exception=True)
        validated_data.save()
        return Response(validated_data.data)
