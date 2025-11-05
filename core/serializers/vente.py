from rest_framework import serializers
from core.models import LigneVente, Vente, Produit, Client

class LigneVenteSerializer(serializers.ModelSerializer):
    produit = serializers.StringRelatedField(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(
        source="produit",
        queryset=Produit.objects.all(),
        write_only=True
    )
    class Meta:
        model = LigneVente
        fields = "__all__"

class VenteSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        source="client",
        queryset=Client.objects.all(),
        write_only=True
    )
    lignes = LigneVenteSerializer(many=True)

    class Meta:
        model = Vente
        fields = "__all__"
        read_only_fields = ("id","date",)

    def create(self, validated_data):
        lignes_data = validated_data.pop("lignes")
        vente = Vente.objects.create(**validated_data)
        for line in lignes_data:
            LigneVente.objects.create(vente=vente, **line)
        return vente
