"""
Export des vues principales de l'application core (version ViewSet unifiée)
"""

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

# Import des modèles et serializers
from core.models import Achat, Vente, Client, Employe
from core.serializers import (
    AchatSerializer, 
    VenteSerializer,
    ClientSerializer,
    EmployeSerializer
)

class BaseViewSet(viewsets.ModelViewSet):
    """ViewSet de base avec fonctionnalités communes"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        queryset = self.get_queryset().order_by('-id')[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AchatViewSet(BaseViewSet):
    queryset = Achat.objects.select_related("fournisseur").prefetch_related("lignes__produit")
    serializer_class = AchatSerializer
    filterset_fields = ["statut", "fournisseur"]
    search_fields = ["id"]

class VenteViewSet(BaseViewSet):
    queryset = Vente.objects.select_related("client").prefetch_related("lignes__produit")
    serializer_class = VenteSerializer
    filterset_fields = ["statut", "client"]
    search_fields = ["id"]

class ClientViewSet(BaseViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    search_fields = ["nom", "telephone", "email"]

class EmployeViewSet(BaseViewSet):
    queryset = Employe.objects.filter(actif=True)
    serializer_class = EmployeSerializer
    search_fields = ["nom", "poste"]

# Vues spéciales
from .dashboard import DashboardStatsView

# Alias pour compatibilité
dashboard_view = DashboardStatsView.as_view()
AchatListView = AchatViewSet.as_view({'get': 'list'})
AchatCreateView = AchatViewSet.as_view({'post': 'create'})
AchatDetailView = AchatViewSet.as_view({'get': 'retrieve'})
AchatUpdateView = AchatViewSet.as_view({'put': 'update'})
# ... (autres alias au même format)

__all__ = [
    # ViewSets principaux
    'AchatViewSet', 'VenteViewSet', 'ClientViewSet', 'EmployeViewSet',
    
    # Vues spéciales
    'DashboardStatsView', 'dashboard_view',
    
    # Alias de compatibilité
    'AchatListView', 'AchatCreateView', 'AchatDetailView', 'AchatUpdateView',
    # ... (autres alias)
]