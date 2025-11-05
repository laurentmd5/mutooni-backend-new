from rest_framework import serializers
from core.models import Vente

class HistoriqueVentesSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_ventes = serializers.DecimalField(max_digits=12, decimal_places=2)
    nombre_ventes = serializers.IntegerField()
    montant_moyen = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        fields = ['date', 'total_ventes', 'nombre_ventes', 'montant_moyen']