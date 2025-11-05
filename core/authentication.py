import logging
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from firebase_admin import auth as fb_auth
from . import firebase  # noqa: ensure app initialized

logger = logging.getLogger(__name__)
User = get_user_model()

class FirebaseAuthentication(authentication.BaseAuthentication):
    """Authentifie via ID-token Firebase."""
    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header or not header.startswith(f"{self.keyword} "):
            return None

        token = header.split(" ", 1)[1]
        try:
            decoded = fb_auth.verify_id_token(token)
        except Exception as e:
            logger.warning(f"Erreur de vérification Firebase : {e}")
            raise exceptions.AuthenticationFailed("ID‑token Firebase invalide")

        uid = decoded.get("uid")
        email = decoded.get("email") or f"{uid}@firebase.local"

        user, _ = User.objects.get_or_create(
            username=uid,
            defaults={"email": email, "is_active": True},
        )

        request.successful_authenticator = self
        return (user, None)
