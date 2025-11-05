from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Fournisseur, Achat
from core.serializers import FournisseurSerializer, AchatSerializer
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    extend_schema_view,
)
from drf_spectacular.types import OpenApiTypes

# ViewSet pour les Fournisseurs (inchangé)
class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom", "telephone", "email"]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrer par nom, téléphone ou email'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# ViewSet pour les Achats avec schéma correctement annoté
@extend_schema_view(
    list=extend_schema(tags=["Achats"]),
    retrieve=extend_schema(tags=["Achats"]),
    create=extend_schema(tags=["Achats"]),
    update=extend_schema(tags=["Achats"]),
    partial_update=extend_schema(tags=["Achats"]),
    destroy=extend_schema(tags=["Achats"]),
)
class AchatViewSet(viewsets.ModelViewSet):
    queryset = Achat.objects.select_related("fournisseur").prefetch_related("lignes__produit")
    serializer_class = AchatSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["statut", "fournisseur"]
    search_fields = ["id"]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='statut',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrer par statut'
            ),
            OpenApiParameter(
                name='fournisseur',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrer par ID fournisseur'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
