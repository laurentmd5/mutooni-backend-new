from rest_framework import serializers
from core.models import Employe, Salaire

class EmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employe
        fields = "__all__"

class SalaireSerializer(serializers.ModelSerializer):
    employe = serializers.StringRelatedField(read_only=True)
    employe_id = serializers.PrimaryKeyRelatedField(
        source="employe",
        queryset=Employe.objects.all(),
        write_only=True
    )
    class Meta:
        model = Salaire
        fields = "__all__"
