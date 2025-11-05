# core/serializers/dashboard.py
from rest_framework import serializers
from datetime import datetime

class DashboardStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques du tableau de bord.
    """
    total_vente = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Total des ventes pour le mois en cours"
    )
    total_achat = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Total des achats pour le mois en cours"
    )
    total_stock = serializers.IntegerField(
        help_text="Nombre total d'articles en stock"
    )


class HistoriqueVentesSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'historique des ventes agrégées par période.
    """
    date = serializers.DateField(
        format='%Y-%m-%d',
        help_text="Date de la période d'agrégation"
    )
    total_ventes = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Somme totale des ventes pour cette période"
    )
    nombre_ventes = serializers.IntegerField(
        help_text="Nombre de ventes effectuées durant cette période"
    )
    montant_moyen = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant moyen des ventes pour cette période"
    )

    class Meta:
        fields = ['date', 'total_ventes', 'nombre_ventes', 'montant_moyen']