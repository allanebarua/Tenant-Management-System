"""Url configs for Generic and function-based views."""
from rest_framework.urls import path

from concepts import class_based_views, function_based_views, generic_views

GENERIC_USER_VIEW = generic_views.KejaUserView.as_view()
KEJA_USER_VIEW = class_based_views.KejaUserView.as_view()
CONTACT_VIEW = class_based_views.ContactView.as_view()

# Function-Based Views
urlpatterns = [
    path('', function_based_views.list_keja_users, name='list-users'),
    path('<int:pk>', function_based_views.list_keja_users, name='list-user'),
    path('create/', function_based_views.create_keja_user, name='create-user'),
    path('update/', function_based_views.update_keja_user, name='update-user'),
    path('delete/<int:pk>', function_based_views.delete_keja_user, name='delete-user'),
    path(
        'create_contact/',
        function_based_views.create_user_contact, name='create-contact'),
    path('list_contacts', function_based_views.get_user_contacts, name='list-contacts'),
]

# Generic views (generics)
urlpatterns = [
    path('users/', GENERIC_USER_VIEW, name='user-list'),
    path('users/<int:pk>', GENERIC_USER_VIEW, name='user-detail'),
]

# Class-based views
urlpatterns = [
    path('users/', KEJA_USER_VIEW, name='user-list'),
    path('users/<int:pk>', KEJA_USER_VIEW, name='user-detail'),
    path('contacts/', CONTACT_VIEW, name='contact-list'),
    path('contacts/<int:pk>', CONTACT_VIEW, name='contact-detail')
]
