from rest_framework import serializers
from core.models import LigneAchat, Achat, Produit, Fournisseur

class LigneAchatSerializer(serializers.ModelSerializer):
    produit = serializers.StringRelatedField(read_only=True)
    produit_id = serializers.PrimaryKeyRelatedField(
        source="produit",
        queryset=Produit.objects.all(),
        write_only=True
    )
    class Meta:
        model = LigneAchat
        fields = "__all__"

class AchatSerializer(serializers.ModelSerializer):
    fournisseur = serializers.StringRelatedField(read_only=True)
    fournisseur_id = serializers.PrimaryKeyRelatedField(
        source="fournisseur",
        queryset=Fournisseur.objects.all(),
        write_only=True
    )
    lignes = LigneAchatSerializer(many=True)

    class Meta:
        model = Achat
        fields = "__all__"
        read_only_fields = ("id","date",)

    def create(self, validated_data):
        lignes_data = validated_data.pop("lignes")
        achat = Achat.objects.create(**validated_data)
        for line in lignes_data:
            LigneAchat.objects.create(achat=achat, **line)
        return achat
