from rest_framework.urls import path

from keja_user import class_based_views, function_based_views, generic_views

KEJA_USER_VIEW = class_based_views.KejaUserView.as_view()
CONTACT_VIEW = class_based_views.ContactView.as_view()

GENERIC_USER_VIEW = generic_views.KejaUserView.as_view()

"""
urlpatterns = [
    path('', function_based_views.list_keja_users, name='list-users'),
    path('<int:pk>', function_based_views.list_keja_users, name='list-user'),
    path('create/', function_based_views.create_keja_user, name='create-user'),
    path('update/', function_based_views.update_keja_user, name='update-user'),
    path('delete/<int:pk>', function_based_views.delete_keja_user, name='delete-user'),
    path('create_contact/', function_based_views.create_user_contact, name='create-contact'),
    path('list_contacts', function_based_views.get_user_contacts, name='list-contacts'),
]
"""

"""
urlpatterns = [
    path('', KEJA_USER_VIEW, name='list-users'),
    path('<int:pk>', KEJA_USER_VIEW, name='list-user'),
    path('create/', KEJA_USER_VIEW, name='create-user'),
    path('update/', KEJA_USER_VIEW, name='update-user'),
    path('delete/<int:pk>', KEJA_USER_VIEW, name='delete-user'),
    path('create_contact/', CONTACT_VIEW, name='create-contact'),
    path('list_contacts', CONTACT_VIEW, name='list-contacts'),
]
"""

urlpatterns = [
    path('', GENERIC_USER_VIEW, name='list-users'),
    path('<int:pk>', GENERIC_USER_VIEW, name='list-user'),
    path('create/', GENERIC_USER_VIEW, name='create-user'),
    path('update/', GENERIC_USER_VIEW, name='update-user'),
    path('delete/<int:pk>', GENERIC_USER_VIEW, name='delete-user'),
    path('create_contact/', CONTACT_VIEW, name='create-contact'),
    path('list_contacts', CONTACT_VIEW, name='list-contacts'),
]
