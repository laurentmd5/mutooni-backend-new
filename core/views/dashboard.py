# core/views/dashboard.py
from rest_framework.views import APIView
from rest_framework.response import Response
from core.models import Vente, Achat, Produit
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from core.serializers.dashboard import DashboardStatsSerializer, HistoriqueVentesSerializer
from drf_spectacular.utils import extend_schema

class DashboardStatsView(APIView):
    """Calcule et sérialise les statistiques pour le tableau de bord"""

    @extend_schema(
        responses=DashboardStatsSerializer
    )
    def get(self, request):
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        ventes_mois = Vente.objects.filter(
            date__date__range=[first_day_of_month, last_day_of_month],
            statut='PAYEE'
        ).aggregate(total_vente=Sum('total'))['total_vente'] or 0

        achats_mois = Achat.objects.filter(
            date__date__range=[first_day_of_month, last_day_of_month],
            statut__in=['PAYE', 'PARTIEL']
        ).aggregate(total_achat=Sum('total'))['total_achat'] or 0

        stock_total = Produit.objects.aggregate(
            total_stock=Sum('stock_actuel')
        )['total_stock'] or 0

        data = {
            'total_vente': float(ventes_mois),
            'total_achat': float(achats_mois),
            'total_stock': int(stock_total)
        }

        serializer = DashboardStatsSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


class HistoriqueVentesView(APIView):
    """Retourne l'historique des ventes agrégées par période"""

    @extend_schema(
        parameters=[
            {
                "name": "jours",
                "in": "query",
                "required": False,
                "schema": {
                    "type": "integer",
                    "default": 30
                },
                "description": "Nombre de jours à analyser"
            },
            {
                "name": "periode",
                "in": "query",
                "required": False,
                "schema": {
                    "type": "string",
                    "enum": ["jour", "semaine", "mois"],
                    "default": "jour"
                },
                "description": "Période d'agrégation"
            }
        ],
        responses=HistoriqueVentesSerializer(many=True)
    )
    def get(self, request):
        jours = int(request.query_params.get('jours', 30))
        periode = request.query_params.get('periode', 'jour')

        date_fin = timezone.now()
        date_debut = date_fin - timedelta(days=jours)

        # Sélection de la fonction de truncation
        trunc_map = {
            'jour': TruncDay,
            'semaine': TruncWeek,
            'mois': TruncMonth
        }
        trunc_func = trunc_map.get(periode, TruncDay)

        queryset = Vente.objects.filter(
            date__range=[date_debut, date_fin],
            statut='PAYEE'
        ).annotate(
            periode=trunc_func('date')
        ).values('periode').annotate(
            total_ventes=Sum('total'),
            nombre_ventes=Count('id'),
            montant_moyen=Avg('total')
        ).order_by('periode')

        serializer = HistoriqueVentesSerializer(queryset, many=True)

        return Response({
            'meta': {
                'periode': periode,
                'jours_analyses': jours,
                'date_debut': date_debut,
                'date_fin': date_fin
            },
            'data': serializer.data
        })