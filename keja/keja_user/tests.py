import base64
from collections import OrderedDict
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from keja.keja_user.models import ADMIN, LANDLORD, PHONE_CONTACT, KejaUser


def create_db_user(user_type):
    return baker.make(
        KejaUser, username='John', password='123', user_type=user_type,
    )


def add_auth_credentials(client, username, password=None, auth_mode='PASSWORD'):
    if auth_mode == 'PASSWORD':
        credentials = f'{username}:{password}'
        base64_credentials = base64.b64encode(
            credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)

        client.credentials(HTTP_AUTHORIZATION=f'Basic {base64_credentials}')

    elif auth_mode == 'TOKEN':
        token = Token.objects.get(user__username=username)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.key}')

    return client


class KejaUserTests(APITestCase):
    """Test user management APIs."""

    @patch('keja.keja_user.models.timezone')
    def test_create_landlord_and_contact(self, timezone_mock):
        """Test creation of a landlord user and his/her contact."""
        dt = timezone.now()
        timezone_mock.now.return_value = dt

        admin = create_db_user(ADMIN)
        self.client = add_auth_credentials(self.client, admin, '123')
        user_data = {
            'username': 'Landlord1',
            'password': '123',
            'user_type': LANDLORD,
            'email': 'landlord1@gmail.com'
        }

        # Create Landlord
        user_response = self.client.post(
            reverse('create-user'), user_data, format='json')
        self.assertEqual(user_response.status_code, status.HTTP_201_CREATED)

        # Create Landlord's contact
        landlord = KejaUser.objects.get(username='Landlord1')
        self.client = add_auth_credentials(self.client, landlord, '123')
        contact_data = {
            'contact_type': PHONE_CONTACT,
            'contact_value': '0790830848',
            'is_active': True
        }
        contact_response = self.client.post(
            reverse('create-contact'), contact_data, format='json')
        self.assertEqual(contact_response.status_code, status.HTTP_201_CREATED)

        # Get the created user data.
        # Landlords can only query data about themselves and their tenants.
        expected_data = [
            OrderedDict([
                ('id', 2),  # The admin account created earlier is id 1
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
                        ('contact_value', '+254790830848'),
                        ('is_active', True)
                    ])
                ])
            ])
        ]
        response = self.client.get(reverse('list-users'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)


class KejaUserClassBasedViewTests(APITestCase):
    @patch('keja.keja_user.models.timezone')
    def test_token_based_authentication(self, timezone_mock):
        """Admin access to the API using token based authentication."""
        dt = timezone.now()
        timezone_mock.now.return_value = dt

        admin = create_db_user(ADMIN)

        # Unauthenticated request.
        response = self.client.get(reverse('list-users'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Password authenticated request
        self.client = add_auth_credentials(
            self.client, admin.username, '123', auth_mode='PASSWORD')
        response = self.client.get(reverse('list-users'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token authenticated request
        self.client = add_auth_credentials(
            self.client, admin.username, auth_mode='TOKEN')
        expected_data = [
            OrderedDict([
                ('id', admin.pk),
                ('username', admin.username),
                ('first_name', ''),
                ('last_name', ''),
                ('email', ''),
                ('is_active', True),
                ('user_type', 'ADMIN'),
                ('landlord', None),
                ('created', dt.date().isoformat()),
                ('user_contacts', [])
            ])
        ]
        response = self.client.get(reverse('list-users'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
