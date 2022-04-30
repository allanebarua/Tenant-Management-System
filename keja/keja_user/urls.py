"""Urls file for keja_user application."""
from rest_framework.urls import path

from keja.keja_user import views

KEJA_USER_VIEW = views.KejaUserView.as_view()
CONTACT_VIEW = views.ContactView.as_view()

urlpatterns = [
    path('', KEJA_USER_VIEW, name='list-users'),
    path('<int:pk>', KEJA_USER_VIEW, name='list-user'),
    path('create/', KEJA_USER_VIEW, name='create-user'),
    path('update/', KEJA_USER_VIEW, name='update-user'),
    path('delete/<int:pk>', KEJA_USER_VIEW, name='delete-user'),
    path('create_contact/', CONTACT_VIEW, name='create-contact'),
    path('list_contacts', CONTACT_VIEW, name='list-contacts'),
]
