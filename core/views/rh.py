from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Employe, Salaire
from core.serializers import EmployeSerializer, SalaireSerializer

class EmployeViewSet(viewsets.ModelViewSet):
    queryset = Employe.objects.all()
    serializer_class = EmployeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom","poste"]

class SalaireViewSet(viewsets.ModelViewSet):
    queryset = Salaire.objects.select_related("employe")
    serializer_class = SalaireSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["periode","employe"]
