import bcrypt
from rest_framework import authentication, exceptions

from keja_user.models import KejaUser


class KejaPasswordAuthentication(authentication.BasicAuthentication):
    """Allow for authentication using hashed passwords."""

    def authenticate_credentials(self, userid, password, request=None):
        """Authenticate the userid and password against username and password."""
        try:
            user = KejaUser.objects.get(username=userid)
        except KejaUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid username/password.')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User is inactive or deleted.')

        try:
            if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                raise exceptions.AuthenticationFailed('Invalid username/password.')
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid username/password.')

        return (user, None)
