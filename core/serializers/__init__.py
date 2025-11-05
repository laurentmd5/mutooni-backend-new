# core/serializers/__init__.py
from .base import (
    CategorieProduitSerializer, ProduitSerializer,
    ClientSerializer, FournisseurSerializer
)
from .vente import VenteSerializer, LigneVenteSerializer
from .achat import AchatSerializer, LigneAchatSerializer
from .stock import MouvementStockSerializer
from .rh import EmployeSerializer, SalaireSerializer
from .transaction import TransactionSerializer

# Ajoutez cette ligne pour importer le sérialiseur du dashboard
from .dashboard import DashboardStatsSerializer

# Optionnel : vous pouvez l'ajouter à __all__ si vous voulez l'exporter explicitement
__all__ = [
    'CategorieProduitSerializer', 'ProduitSerializer',
    'ClientSerializer', 'FournisseurSerializer',
    'VenteSerializer', 'LigneVenteSerializer',
    'AchatSerializer', 'LigneAchatSerializer',
    'MouvementStockSerializer',
    'EmployeSerializer', 'SalaireSerializer',
    'TransactionSerializer',
    'DashboardStatsSerializer'  # Ajout du nouveau sérialiseur
]