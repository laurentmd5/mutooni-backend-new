from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.models import CategorieProduit, Produit, MouvementStock
from core.serializers import (
    CategorieProduitSerializer, ProduitSerializer, MouvementStockSerializer
)

class CategorieProduitViewSet(viewsets.ModelViewSet):
    queryset = CategorieProduit.objects.all()
    serializer_class = CategorieProduitSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom"]

class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nom"]
    filterset_fields = ["categorie"]

class MouvementStockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MouvementStock.objects.select_related("produit")
    serializer_class = MouvementStockSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["produit","type","date"]
