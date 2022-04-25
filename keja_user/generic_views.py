from django.db.models import Q
from rest_framework import exceptions, generics
from rest_framework.response import Response

from keja_user.models import LANDLORD, TENANT, KejaUser
from keja_user.serializers import KejaUserSerializer


class KejaUserView(
        generics.ListCreateAPIView,
        generics.RetrieveUpdateDestroyAPIView):

    queryset = KejaUser.objects.all()
    serializer_class = KejaUserSerializer

    def list(self, request, *args, **kwargs):
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

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if not request.user.is_staff and user != request.user:
            raise exceptions.PermissionDenied(
                f'user {request.user.id} cannot update user {user.id}')

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def check_object_permissions(self, request, obj):
        permitted = (
            request.user.is_staff
            or request.user == obj
            or request.user == obj.landlord
        )

        if not permitted:
            raise exceptions.PermissionDenied(
                f'user {request.user.id} cannot retrive user {obj.id}')
