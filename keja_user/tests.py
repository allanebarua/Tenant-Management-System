import base64
from collections import OrderedDict
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.test import APITestCase

from keja_user.models import ADMIN, LANDLORD, PHONE_CONTACT, KejaUser


def create_db_user(user_type):
    return baker.make(
        KejaUser, username='John', password='123', user_type=user_type,
    )


def add_auth_credentials(client, username, password):
    credentials = f'{username}:{password}'
    base64_credentials = base64.b64encode(
        credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)
    
    client.credentials(HTTP_AUTHORIZATION=f'Basic {base64_credentials}')
    return client


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=['testserver'])
class KejaUserTests(APITestCase):
    """Test user management APIs."""

    @patch('keja_user.models.timezone')
    def test_create_landlord_and_contact(self, timezone_mock):
        """Test creation of a landlord user and his/her contact."""
        dt = timezone.now()
        timezone_mock.now.return_value = dt

        admin = create_db_user(ADMIN)
        self.client = add_auth_credentials(self.client, admin.username, '123')
        user_data = {
            'username': 'Landlord1',
            'password': '123',
            'user_type': LANDLORD,
            'email': 'landlord1@gmail.com'
        }

        # Create Landlord
        user_response = self.client.post(reverse('create-user'), user_data, format='json')
        self.assertEqual(user_response.status_code, status.HTTP_201_CREATED)

        # Create Landlord's contact
        self.client = add_auth_credentials(self.client, 'Landlord1', '123')
        contact_data = {
            'contact_type': PHONE_CONTACT,
            'contact_value': '0790830848',
            'is_active': True
        }
        contact_response = self.client.post(reverse('create-contact'), contact_data, format='json')
        self.assertEqual(contact_response.status_code, status.HTTP_201_CREATED)

        # Get the created user data.
        # Landlords can only query data about themselves and their tenants.
        expected_data = [
            OrderedDict([
                ('id', 2), # The admin account created earlier is id 1
                ('username', 'Landlord1'),
                ('first_name', ''),
                ('last_name', ''),
                ('email', 'landlord1@gmail.com'),
                ('is_active', True),
                ('user_type', 'LANDLORD'),
                ('landlord', None),
                ('created', dt.date().isoformat()),
                ('user_contacts', [
                    OrderedDict([
                        ('owner', 'Landlord1'),
                        ('contact_type', 'PHONE'),
                        ('contact_value', '+254790830848')
                    ])
                ])
            ])
        ]
        get_response = self.client.get(reverse('list-users'))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data, expected_data)
