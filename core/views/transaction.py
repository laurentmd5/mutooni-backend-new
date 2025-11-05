from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Transaction
from core.serializers import TransactionSerializer

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type","module","date"]
