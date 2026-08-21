"""Lets someone log in with either their email or their company employee
number — in practice, people don't always remember which one a given form
wants, and both already uniquely identify one account (see
accounts/models.py:find_user_by_login_identifier). Registered in
config/settings.py's AUTHENTICATION_BACKENDS in place of the default
ModelBackend; everything else about Django's own authentication (password
hashing/checking, the is_active check, timing-attack mitigation on a
miss) is unchanged — only how the identifier is resolved to a user."""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .models import find_user_by_login_identifier


class EmployeeNumberOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = find_user_by_login_identifier(username)
        if user is None:
            # Same dummy hash-and-compare as the stock ModelBackend when no
            # account matches — keeps a miss and a wrong password taking
            # about the same amount of time either way.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
