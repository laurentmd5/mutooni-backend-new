from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Client, Vente
from core.serializers import ClientSerializer, VenteSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom","telephone","email"]

class VenteViewSet(viewsets.ModelViewSet):
    queryset = Vente.objects.select_related("client").prefetch_related("lignes__produit")
    serializer_class = VenteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["statut","client"]
    search_fields = ["id"]
