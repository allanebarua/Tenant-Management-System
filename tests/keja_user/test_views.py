"""Tests for user and contacts management utilities."""
import base64
from collections import OrderedDict
from unittest.mock import MagicMock, patch

from model_bakery import baker
from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from django.urls import reverse
from django.utils import timezone
from keja.config import asgi, wsgi  # noqa
from keja.keja_user.models import (
    ADMIN, LANDLORD, PHONE_CONTACT, TENANT, Contact, KejaUser)


def create_db_user(user_type, landlord=None):
    """Create a system user."""
    landlord = landlord if user_type == TENANT else None
    return baker.make(
        KejaUser, username=f'{user_type}-John', password='123',
        user_type=user_type, landlord=landlord
    )


def add_auth_credentials(client, user, password=None, auth_mode='PASSWORD'):
    """Add authentication information to the client."""
    if auth_mode == 'PASSWORD':
        credentials = f'{user.username}:{password}'
        base64_credentials = base64.b64encode(
            credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)

        client.credentials(HTTP_AUTHORIZATION=f'Basic {base64_credentials}')

    elif auth_mode == 'TOKEN':
        token = Token.objects.get(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.key}')

    return client


class KejaUserViewTests(APITestCase):
    """Test user management APIs."""

    @patch('keja.keja_user.models.timezone')
    def test_token_based_authentication(self, timezone_mock):
        """Test admin access to the API using token based authentication."""
        dt = timezone.now()
        timezone_mock.now.return_value = dt

        admin = create_db_user(ADMIN)

        # Unauthenticated request.
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Password authenticated request
        self.client = add_auth_credentials(
            self.client, admin, '123', auth_mode='PASSWORD')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token authenticated request
        self.client = add_auth_credentials(
            self.client, admin, auth_mode='TOKEN')
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
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

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
            reverse('user-list'), user_data, format='json')
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
            reverse('contact-list'), contact_data, format='json')
        self.assertEqual(contact_response.status_code, status.HTTP_201_CREATED)

        # Get the created user data.
        # Landlords can only query data about themselves and their tenants.
        expected_data = [
            OrderedDict([
                ('id', landlord.id),
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
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_list_users(self):
        """Test list users using different user account types."""
        admin = create_db_user(ADMIN)
        landlord = create_db_user(LANDLORD)
        tenant = create_db_user(TENANT, landlord)

        # An admin account can retrieve all user accounts.
        self.client = add_auth_credentials(self.client, admin, '123')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # A landlord can retrive his/her account + accounts for their tenants.
        self.client = add_auth_credentials(self.client, landlord, '123')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # A tenant can retrive his/her own account.
        self.client = add_auth_credentials(self.client, tenant, '123')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_users(self):
        """Test retrive single user."""
        admin = create_db_user(ADMIN)
        landlord = create_db_user(LANDLORD)
        tenant = create_db_user(TENANT, landlord)

        # Admin retrieves tenant account.
        expected_response = {
            'id': tenant.id,
            'username':
            'TENANT-John',
            'first_name': '',
            'last_name': '',
            'email': '',
            'is_active': True,
            'user_type': 'TENANT',
            'landlord': 'LANDLORD-John',
            'created': '2022-05-06',
            'user_contacts': []
        }
        self.client = add_auth_credentials(self.client, admin, '123')
        response = self.client.get(reverse('user-detail', args=(tenant.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_response)

        # A tenant tries to retrieve admin's account.
        self.client = add_auth_credentials(self.client, tenant, '123')
        response = self.client.get(reverse('user-detail', args=(admin.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('keja.keja_user.models.timezone')
    def test_update_user(self, timezone_mock):
        """Test update user through the user API."""
        dt = timezone.now()
        timezone_mock.now.return_value = dt

        admin = create_db_user(ADMIN)
        landlord = create_db_user(LANDLORD)
        tenant = create_db_user(TENANT, landlord)

        # An admin can update all accounts.
        self.client = add_auth_credentials(self.client, admin, '123')
        user_data = {'first_name': 'allan'}
        response = self.client.patch(reverse(
            'user-detail', args=(landlord.id,)), user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = {
            'id': landlord.pk,
            'username': landlord.username,
            'first_name': 'allan',
            'last_name': '',
            'email': '',
            'is_active': True,
            'user_type': 'LANDLORD',
            'landlord': None,
            'created': dt.date().isoformat(),
            'user_contacts': []
        }
        self.assertEqual(response.data, expected_response)

        # landlord cannot update tenant accounts.
        self.client = add_auth_credentials(self.client, landlord, '123')
        user_data = {'first_name': 'allan'}
        response = self.client.patch(reverse(
            'user-detail', args=(tenant.id,)), user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            str(response.data['detail']),
            f'user {landlord.pk} cannot update user {tenant.pk}')

    def test_delete_user(self):
        """Test deletion of a user."""
        admin = create_db_user(ADMIN)
        landlord = create_db_user(LANDLORD)

        # Only Admins can delete user accounts.
        self.client = add_auth_credentials(self.client, landlord, '123')
        response = self.client.delete(reverse('user-detail', args=(landlord.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            str(response.data['detail']),
            'You do not have permission to perform this action.')
        self.assertEqual(KejaUser.objects.count(), 2)

        # Delete account using an admin account.
        self.client = add_auth_credentials(self.client, admin, '123')
        response = self.client.delete(reverse('user-detail', args=(landlord.id,)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(KejaUser.objects.count(), 1)

    def test_create_landlord_without_an_email_address(self):
        """Test create a landlord without an email address."""
        admin = create_db_user(ADMIN)
        self.client = add_auth_credentials(self.client, admin, '123')
        user_data = {
            'username': 'Landlord1',
            'password': '123',
            'user_type': LANDLORD
        }
        resp = self.client.post(reverse('user-list'), user_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(resp.data['email'][0]),
            'A Landlord should have an email address.')

    def test_landlord_can_only_create_tenant_accounts(self):
        """Test landlord can only create tenant accounts."""
        landlord = create_db_user(LANDLORD)
        self.client = add_auth_credentials(self.client, landlord, '123')
        user_data = {
            'username': 'Landlord1',
            'password': '123',
            'user_type': LANDLORD,
            'email': 'allan@gmail.com'
        }
        resp = self.client.post(reverse('user-list'), user_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(resp.data['non_field_errors']),
            'A Landlord can only create tenant user accounts.')

    def test_admin_cannot_create_tenant_accounts(self):
        """Test Admin cannot create tenant accounts."""
        admin = create_db_user(ADMIN)
        self.client = add_auth_credentials(self.client, admin, '123')
        user_data = {
            'username': 'tenant1',
            'password': '123',
            'user_type': TENANT,
        }
        resp = self.client.post(reverse('user-list'), user_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(resp.data['non_field_errors']),
            'An Admin cannot create tenant user accounts.')

    def test_user_filters(self):
        """Test user filters."""
        admin = create_db_user(ADMIN)
        create_db_user(LANDLORD)

        self.client = add_auth_credentials(self.client, admin, '123')
        url = reverse('user-list') + '?is_active=True'
        resp = self.client.get(url)
        self.assertEqual(len(resp.data), 2)

        url = reverse('user-list') + '?is_active=False'
        resp = self.client.get(url)
        self.assertEqual(len(resp.data), 0)


class ContactViewTests(APITestCase):
    """Test contacts management views."""

    def test_create_phone_contact(self):
        """Test creation of phone contacts."""
        admin = create_db_user(ADMIN)
        contacts_data = {
            'contact_type': 'PHONE',
            'contact_value': '0790830848',
            'is_active': True
        }

        # Successfuly create phone contact.
        expected_response = {
            'contact_type': 'PHONE',
            'contact_value': '+254790830848',
            'is_active': True,
            'owner': admin.username
        }

        self.client = add_auth_credentials(self.client, admin, '123')
        resp = self.client.post(reverse('contact-list'), contacts_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data, expected_response)

        # Invalid phone contact
        contacts_data = {
            'contact_type': 'PHONE',
            'contact_value': 'K',
            'is_active': True
        }
        self.client = add_auth_credentials(self.client, admin, '123')
        resp = self.client.post(reverse('contact-list'), contacts_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(resp.data['non_field_errors'][0]), 'Invalid phone number supplied.')

    def test_create_email_contact(self):
        """Test creation of email contacts."""
        admin = create_db_user(ADMIN)
        contacts_data = {
            'contact_type': 'EMAIL',
            'contact_value': 'allan@gmail.com',
            'is_active': True
        }

        # Successfuly create email contact.
        expected_response = {
            'contact_type': 'EMAIL',
            'contact_value': 'allan@gmail.com',
            'is_active': True,
            'owner': admin.username
        }
        self.client = add_auth_credentials(self.client, admin, '123')
        resp = self.client.post(reverse('contact-list'), contacts_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data, expected_response)

        # Invalid email contact
        contacts_data = {
            'contact_type': 'EMAIL',
            'contact_value': 'allan',
            'is_active': True
        }
        self.client = add_auth_credentials(self.client, admin, '123')
        resp = self.client.post(reverse('contact-list'), contacts_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(resp.data['non_field_errors'][0]), 'Enter a valid email address.')

    def test_update_contact(self):
        """Test update of contacts."""
        tenant = create_db_user(TENANT)
        contacts_data = {
            'contact_type': 'PHONE',
            'contact_value': '0790830848',
            'is_active': True
        }

        expected_response = {
            'contact_type': 'PHONE',
            'contact_value': '+254790830848',
            'is_active': False,
            'owner': tenant.username
        }
        self.client = add_auth_credentials(self.client, tenant, '123')
        self.client.post(reverse('contact-list'), contacts_data)

        contact = Contact.objects.get(owner=tenant)
        self.assertTrue(contact.is_active)
        resp = self.client.patch(reverse(
            'contact-detail', args=(contact.id,)), {'is_active': False})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, expected_response)
        contact.refresh_from_db()
        self.assertFalse(contact.is_active)

        # Non-admin user cannot update contacts for other users.
        landlord = create_db_user(LANDLORD)
        self.client = add_auth_credentials(self.client, landlord, '123')
        resp = self.client.patch(reverse(
            'contact-detail', args=(contact.id,)), {'is_active': False})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_contacts(self):
        """Test retrieve user contacts."""
        admin = create_db_user(ADMIN)
        landlord = create_db_user(LANDLORD)
        tenant = create_db_user(TENANT, landlord)

        baker.make(
            Contact, owner=admin, contact_type='PHONE', contact_value='0790000000',
        )
        baker.make(
            Contact, owner=landlord, contact_type='PHONE', contact_value='0790000001',
        )
        baker.make(
            Contact, owner=tenant, contact_type='PHONE', contact_value='0790000002',
        )

        # Admin can retrieve all the three contacts.
        self.client = add_auth_credentials(self.client, admin, '123')
        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 3)

        # Landlord can retrieve his/her contact + contacts for his/her tenants.
        self.client = add_auth_credentials(self.client, landlord, '123')
        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

        # tenant can only retrieve his/her contact.
        self.client = add_auth_credentials(self.client, tenant, '123')
        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_contact_filters(self):
        """Test contact filters."""
        admin = create_db_user(ADMIN)
        baker.make(
            Contact, owner=admin, contact_type='PHONE', contact_value='0790000000',
            is_active=True
        )

        # Query active contacts.
        self.client = add_auth_credentials(self.client, admin, '123')
        url = reverse('contact-list') + '?is_active=True'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

        # Query inactive contacts.
        self.client = add_auth_credentials(self.client, admin, '123')
        url = reverse('contact-list') + '?is_active=False'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

        # wrong filter
        self.client = add_auth_credentials(self.client, admin, '123')
        url = reverse('contact-list') + '?is_active=invalid'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)


class AuthenticationTests(APITestCase):
    """Password authentication tests."""

    def test_user_not_found(self):
        """Test attemped login with ghost user."""
        mock_user = MagicMock()
        mock_user.username = 'magicuser'
        mock_user.password = '123'

        self.client = add_auth_credentials(self.client, mock_user, '123')
        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(resp.data['detail']), 'Invalid username/password.')

    def test_inactive_user(self):
        """Test attempted login for inactive user."""
        admin = create_db_user(ADMIN)
        admin.is_active = False
        admin.save()
        self.client = add_auth_credentials(self.client, admin, '123')

        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(resp.data['detail']), 'User is inactive or deleted.')

    def test_active_user_wrong_password(self):
        """Test attempted login with wrong password."""
        admin = create_db_user(ADMIN)

        self.client = add_auth_credentials(self.client, admin, 'wrongpass')

        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(resp.data['detail']), 'Invalid username/password.')

    @patch('keja.keja_user.authentication.bcrypt')
    def test_brcypt_error(self, bcrypt_mock):
        """Test bcrypt hashing error."""
        bcrypt_mock.checkpw.side_effect = Exception('error occured')

        admin = create_db_user(ADMIN)
        self.client = add_auth_credentials(self.client, admin, '123')
        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(resp.data['detail']), 'Invalid username/password.')

    def test_user_authenticated_successfully(self):
        """Test user authenticated successfully."""
        admin = create_db_user(ADMIN)
        self.client = add_auth_credentials(self.client, admin, '123')

        resp = self.client.get(reverse('contact-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
