from rest_framework import serializers
from core.models import CategorieProduit, Produit, Client, Fournisseur

class CategorieProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieProduit
        fields = "__all__"

class ProduitSerializer(serializers.ModelSerializer):
    categorie = CategorieProduitSerializer(read_only=True)
    categorie_id = serializers.PrimaryKeyRelatedField(
        source="categorie",
        queryset=CategorieProduit.objects.all(),
        write_only=True
    )
    class Meta:
        model = Produit
        fields = "__all__"

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"

class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = "__all__"
