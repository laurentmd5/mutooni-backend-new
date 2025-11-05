from rest_framework import serializers
from core.models import MouvementStock, Produit

class MouvementStockSerializer(serializers.ModelSerializer):
    produit = serializers.StringRelatedField(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(
        source="produit",
        queryset=Produit.objects.all(),
        write_only=True
    )
    class Meta:
        model = MouvementStock
        fields = "__all__"
