from django.contrib import admin
from .models import (
    CategorieProduit, Produit, Client, Fournisseur, Vente, LigneVente,
    Achat, LigneAchat, MouvementStock, Employe, Salaire, Transaction
)

@admin.register(CategorieProduit)
class CategorieProduitAdmin(admin.ModelAdmin):
    list_display = ("id", "nom")
    search_fields = ("nom",)

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "categorie", "stock_actuel", "prix_unitaire", "seuil_min")
    list_filter = ("categorie",)
    search_fields = ("nom",)

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "telephone", "email", "solde")
    search_fields = ("nom","telephone","email")

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ("id","nom","telephone","email","solde")
    search_fields = ("nom","telephone","email")

class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0

@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ("id","client","date","total","montant_paye","statut")
    list_filter = ("statut","date")
    inlines = [LigneVenteInline]

class LigneAchatInline(admin.TabularInline):
    model = LigneAchat
    extra = 0

@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    list_display = ("id","fournisseur","date","total","montant_paye","statut")
    list_filter = ("statut","date")
    inlines = [LigneAchatInline]

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("id","produit","type","quantite","date","source_type","source_id")
    list_filter = ("type","date")

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ("id","nom","poste","salaire_base","date_embauche","actif")
    list_filter = ("poste","actif")

@admin.register(Salaire)
class SalaireAdmin(admin.ModelAdmin):
    list_display = ("id","employe","periode","brut","net","montant_paye","date_paiement")
    list_filter = ("periode",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id","type","module","reference_id","montant","date")
    list_filter = ("type","module","date")