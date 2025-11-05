from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "role", "is_active", "date_joined"
        )
        read_only_fields = ("id", "date_joined", "is_active")


# ────────────────────────────────────────────────────────────────
# ➕  Nouveaux serializers uniquement pour la doc & la validation
# ────────────────────────────────────────────────────────────────
class FirebaseAuthRequestSerializer(serializers.Serializer):
    id_token = serializers.CharField(help_text="ID‑token retourné par Firebase Auth")


class TokenPairSerializer(serializers.Serializer):
    access  = serializers.CharField(help_text="JWT d'accès (SimpleJWT)")
    refresh = serializers.CharField(help_text="JWT de rafraîchissement")
