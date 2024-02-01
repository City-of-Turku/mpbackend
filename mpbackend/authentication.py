from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


def is_token_expired(token):
    min_age = timezone.now() - timedelta(hours=settings.TOKEN_EXPIRED_AFTER_HOURS)
    expired = token.created < min_age
    return expired


class ExpiringTokenAuthentication(TokenAuthentication):
    """Same as in DRF, but also handle Token expiration.
    An expired Token will be removed.
    Raise AuthenticationFailed as needed, which translates
    to a 401 status code automatically.
    https://stackoverflow.com/questions/14567586
    """

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        if not token.user.is_active:
            raise AuthenticationFailed("User inactive or deleted")

        if is_token_expired(token):
            token.delete()
            raise AuthenticationFailed("Token has expired and has been deleted")

        return (token.user, token)
