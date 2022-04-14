from rest_framework.urls import path

from keja_user import function_views

urlpatterns = [
    path('', function_views.list_keja_users, name='list-users'),
    path('<int:pk>', function_views.list_keja_users, name='list-user'),
    path('create/', function_views.create_keja_user, name='create-user'),
    path('update/', function_views.update_keja_user, name='update-user'),
    path('delete/<int:pk>', function_views.delete_keja_user, name='delete-user'),
    path('create_contact/', function_views.create_user_contact, name='create-contact'),
    path('list_contacts', function_views.get_user_contacts, name='list-contacts'),
]
