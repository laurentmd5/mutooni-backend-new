import os
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials

from users.models import User
from users.serializers import UserSerializer, FirebaseAuthRequestSerializer, TokenPairSerializer
from users.permissions import IsAdmin


User = get_user_model()

# Initialisation Firebase si nécessaire
if not firebase_admin._apps:
    cred_path = Path(__file__).resolve().parent.parent / 'firebase' / 'serviceAccountKey.json'
    firebase_admin.initialize_app(credentials.Certificate(cred_path))


class FirebaseAuthView(APIView):
    """
    Authentification via Firebase (id_token).
    Retourne un JWT local.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=FirebaseAuthRequestSerializer,
        responses={
            200: TokenPairSerializer,
            400: OpenApiResponse(description="id_token manquant"),
            401: OpenApiResponse(description="Token Firebase invalide"),
        },
        summary="Connexion avec Firebase",
        tags=["Auth"],
    )
    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "id_token manquant"}, status=400)

        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token["uid"]
            email = decoded_token.get("email")

            user, created = User.objects.get_or_create(email=email, defaults={"username": email})

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD complet sur le modèle User.

    - LIST & CREATE : réservés aux administrateurs (IsAdmin).
    - RETRIEVE / UPDATE / PARTIAL_UPDATE / DESTROY :
      l'utilisateur peut accéder/éditer *uniquement* son propre profil.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ("list", "create"):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return super().get_queryset()
        return self.queryset.filter(id=user.id)

    def perform_create(self, serializer):
        serializer.save(is_active=True)


class PingView(APIView):
    """
    Vue très simple pour vérifier que l'API répond.

    Accessible sans authentification (AllowAny).
    Renvoie {"ping": "pong"}.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Test de disponibilité de l'API",
        description="Renvoie « pong » afin de confirmer que l'API Mutooni est opérationnelle.",
        responses={200: OpenApiResponse(description='Pong!')},
        tags=["Debug"]
    )
    def get(self, request):
        return Response({"ping": "pong"})
