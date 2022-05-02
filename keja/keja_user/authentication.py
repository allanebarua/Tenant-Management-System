"""Project's customized authentication classes."""
import bcrypt

from keja.keja_user.models import KejaUser
from rest_framework import authentication, exceptions


class KejaPasswordAuthentication(authentication.BasicAuthentication):
    """Authenticate Using hashed password."""

    def authenticate_credentials(self, userid, password, request=None):
        """Authenticate Using hashed password."""
        try:
            user = KejaUser.objects.get(username=userid)
        except KejaUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid username/password.')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User is inactive or deleted.')

        try:
            if not bcrypt.checkpw(
                    password.encode('utf-8'), user.password.encode('utf-8')):
                raise exceptions.AuthenticationFailed('Invalid username/password.')
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid username/password.')

        return (user, None)


class KejaTokenAuthentication(authentication.TokenAuthentication):
    """Authenticate using a token."""

    keyword = 'Bearer'
