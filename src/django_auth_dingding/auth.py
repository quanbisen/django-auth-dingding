import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from mozilla_django_oidc.utils import import_from_settings

LOGGER = logging.getLogger(__name__)


class DingdingAuthenticationBackend(ModelBackend):
    """Override Django's authentication."""

    def __init__(self, *args, **kwargs):
        self.UserModel = get_user_model()

    @staticmethod
    def get_settings(attr, *args):
        return import_from_settings(attr, *args)

    def create_user(self, claims):
        """Return object for a newly created user account."""
        username = claims.get("name")
        email = claims.get("email")
        if email:
            username = email.split("@")[0]
        return self.UserModel.objects.create_user(username=username, display=claims.get("name"),
                                                  email=email, ding_user_id=claims.get("userid"))

    def update_user(self, user, claims):
        """Update existing user with new claims, if necessary save, and return user"""
        username = claims.get("name")
        email = claims.get("email", "")
        if email:
            username = email.split("@")[0]
        user.username = username
        user.email = email
        user.display = claims.get("name")
        user.save()
        return user

    def authenticate(self, request, **kwargs):
        """authenticate success will return a user."""
        claim = kwargs.get("auth_dingding_user")
        if not claim:
            return None
        try:
            user = self.UserModel.objects.get(ding_user_id=claim.get("userid"))
            user = self.update_user(user, claim)
        except self.UserModel.DoesNotExist as _:
            user = self.create_user(claim)
        return user
