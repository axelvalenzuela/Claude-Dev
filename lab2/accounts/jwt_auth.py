"""JWT-based authentication for the employee/admin web portal — see
docs/adr/0011-jwt-web-authentication.md for why this replaces Django's
session login for everything except /admin/, which keeps its own
session-based login untouched (django.contrib.admin has no supported way
to run on a stateless token instead of a session).

Two tokens are issued together at login (accounts/views.py:JWTLoginView),
both as HttpOnly cookies so JavaScript on the page can never read them:

- **Access token** (JWT_ACCESS_TOKEN_LIFETIME, short-lived): proves who
  the request is from. Verified on every request by
  JWTAuthenticationMiddleware below; never checked against the database
  beyond looking the user up by id, which is what makes it fast enough to
  check on every request.
- **Refresh token** (JWT_REFRESH_TOKEN_LIFETIME, long-lived): only used to
  silently mint a new access token once the old one expires, so a
  session doesn't visibly end every JWT_ACCESS_TOKEN_LIFETIME minutes.
  Carries a `jti` (unique id) so a single refresh token can be revoked
  early via BlacklistedToken — the only way to make a specific token
  stop working before its own `exp`, since JWTs are otherwise stateless.
"""
import uuid
from datetime import datetime, timezone

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


def _now():
    return datetime.now(timezone.utc)


def generate_access_token(user):
    now = _now()
    payload = {
        # PyJWT requires "sub" to be a string (RFC 7519) — cast back to
        # int in _active_user() before the pk lookup.
        "sub": str(user.pk),
        "token_type": "access",
        "iat": now,
        "exp": now + settings.JWT_ACCESS_TOKEN_LIFETIME,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token(user):
    now = _now()
    payload = {
        "sub": str(user.pk),
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + settings.JWT_REFRESH_TOKEN_LIFETIME,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode(token, expected_type):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("token_type") != expected_type:
        return None
    return payload


def decode_access_token(token):
    return _decode(token, "access")


def decode_refresh_token(token):
    return _decode(token, "refresh")


def _active_user(user_id):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=int(user_id))
    except (UserModel.DoesNotExist, TypeError, ValueError):
        return None
    return user if user.is_active else None


def user_from_access_token(token):
    payload = decode_access_token(token)
    if payload is None:
        return None
    return _active_user(payload["sub"])


def _is_refresh_token_blacklisted(jti):
    from .models import BlacklistedToken

    return BlacklistedToken.objects.filter(jti=jti).exists()


def user_and_new_access_token_from_refresh_token(token):
    """Validates a refresh token cookie for the silent-refresh path
    (JWTAuthenticationMiddleware) — returns (user, new_access_token), or
    (None, None) if the refresh token is missing, expired, forged, or was
    blacklisted by an earlier logout."""
    payload = decode_refresh_token(token)
    if payload is None:
        return None, None
    if _is_refresh_token_blacklisted(payload["jti"]):
        return None, None
    user = _active_user(payload["sub"])
    if user is None:
        return None, None
    return user, generate_access_token(user)


def revoke_refresh_token(request):
    """Blacklists the current refresh token (if any) so it can't be used
    to silently mint new access tokens after logout — called from
    JWTLogoutView. This is the closest a stateless JWT gets to "logged
    out right now" instead of "logged out once it expires on its own"."""
    from .models import BlacklistedToken

    payload = decode_refresh_token(request.COOKIES.get(REFRESH_COOKIE_NAME))
    if payload is None:
        return
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    BlacklistedToken.objects.get_or_create(jti=payload["jti"], defaults={"expires_at": expires_at})


def _cookie_kwargs(max_age):
    return {
        "max_age": int(max_age.total_seconds()),
        "httponly": True,
        "secure": settings.HTTPS_ENABLED,
        "samesite": "Lax",
    }


def set_auth_cookies(response, user):
    """Issues a fresh access+refresh token pair — called on successful
    login/signup (accounts/views.py)."""
    response.set_cookie(
        ACCESS_COOKIE_NAME, generate_access_token(user), **_cookie_kwargs(settings.JWT_ACCESS_TOKEN_LIFETIME)
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME, generate_refresh_token(user), **_cookie_kwargs(settings.JWT_REFRESH_TOKEN_LIFETIME)
    )


def set_access_cookie(response, access_token):
    """Replaces just the access-token cookie — used by the silent-refresh
    path (JWTAuthenticationMiddleware), which never issues a new refresh
    token (that would extend a session past JWT_REFRESH_TOKEN_LIFETIME
    indefinitely just by staying active)."""
    response.set_cookie(ACCESS_COOKIE_NAME, access_token, **_cookie_kwargs(settings.JWT_ACCESS_TOKEN_LIFETIME))


def clear_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)


class JWTAuthenticationMiddleware:
    """Overrides request.user from the JWT cookies for every route except
    /admin/ (Django Admin keeps its own session-based login — see the
    module docstring). Only acts when an access or refresh token cookie is
    actually present; a request with neither is left exactly as
    AuthenticationMiddleware already resolved it, which is what lets
    Client.login()/force_login() in tests keep working unchanged — those
    set up a session directly and never go through this cookie check, the
    same way a real /admin/ session never does."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        new_access_token = None
        if not request.path.startswith("/admin/"):
            new_access_token = self._authenticate(request)

        response = self.get_response(request)

        if new_access_token:
            set_access_cookie(response, new_access_token)

        return response

    def _authenticate(self, request):
        access_token = request.COOKIES.get(ACCESS_COOKIE_NAME)
        user = user_from_access_token(access_token)
        if user is not None:
            request.user = user
            return None

        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not refresh_token:
            return None

        user, new_access_token = user_and_new_access_token_from_refresh_token(refresh_token)
        if user is None:
            return None

        request.user = user
        return new_access_token
