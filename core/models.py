from django.db import models

class CategorieProduit(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom

class Produit(models.Model):
    nom            = models.CharField(max_length=150)
    categorie      = models.ForeignKey(CategorieProduit, on_delete=models.SET_NULL, null=True)
    unite          = models.CharField(max_length=20)
    prix_unitaire  = models.DecimalField(max_digits=10, decimal_places=2)
    seuil_min      = models.IntegerField(default=0)
    stock_actuel   = models.IntegerField(default=0)

    def __str__(self):
        return self.nom

class Client(models.Model):
    nom       = models.CharField(max_length=120)
    telephone = models.CharField(max_length=30, blank=True)
    email     = models.EmailField(blank=True, null=True)
    adresse   = models.TextField(blank=True)
    solde     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.nom

class Fournisseur(models.Model):
    nom       = models.CharField(max_length=120)
    telephone = models.CharField(max_length=30, blank=True)
    email     = models.EmailField(blank=True, null=True)
    adresse   = models.TextField(blank=True)
    solde     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.nom

class Vente(models.Model):
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('PAYEE', 'Payée'),
        ('ANNULEE', 'Annulée'),
    ]
    client         = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    date           = models.DateTimeField(auto_now_add=True)
    total          = models.DecimalField(max_digits=12, decimal_places=2)
    montant_paye   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mode_paiement  = models.CharField(max_length=50, blank=True)
    statut         = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_COURS')

    def __str__(self):
        return f"Vente #{self.id} - {self.client.nom if self.client else 'N/A'}"

class LigneVente(models.Model):
    vente         = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit       = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True)
    quantite      = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    remise        = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Achat(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYE', 'Payé'),
        ('PARTIEL', 'Partiellement payé'),
        ('ANNULE', 'Annulé'),
    ]
    fournisseur    = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True)
    date           = models.DateTimeField(auto_now_add=True)
    total          = models.DecimalField(max_digits=12, decimal_places=2)
    montant_paye   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut         = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')

    def __str__(self):
        return f"Achat #{self.id} - {self.fournisseur.nom if self.fournisseur else 'N/A'}"

class LigneAchat(models.Model):
    achat          = models.ForeignKey(Achat, on_delete=models.CASCADE, related_name='lignes')
    produit        = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True)
    quantite       = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire  = models.DecimalField(max_digits=10, decimal_places=2)

class MouvementStock(models.Model):
    TYPE_CHOICES = [('ENTREE','Entrée'), ('SORTIE','Sortie')]
    produit      = models.ForeignKey(Produit, on_delete=models.CASCADE)
    date         = models.DateTimeField(auto_now_add=True)
    type         = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite     = models.DecimalField(max_digits=10, decimal_places=2)
    source_type  = models.CharField(max_length=30, blank=True)  # VENTE / ACHAT / MANUEL
    source_id    = models.IntegerField(blank=True, null=True)

class Employe(models.Model):
    nom           = models.CharField(max_length=120)
    poste         = models.CharField(max_length=80)
    salaire_base  = models.DecimalField(max_digits=10, decimal_places=2)
    date_embauche = models.DateField()
    actif         = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

class Salaire(models.Model):
    employe       = models.ForeignKey(Employe, on_delete=models.CASCADE)
    periode       = models.CharField(max_length=20)  # ex: 2025-06
    brut          = models.DecimalField(max_digits=10, decimal_places=2)
    net           = models.DecimalField(max_digits=10, decimal_places=2)
    montant_paye  = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)

class Transaction(models.Model):
    TYPE_CHOICES = [('RECETTE','Recette'), ('DEPENSE','Dépense')]
    date          = models.DateTimeField(auto_now_add=True)
    type          = models.CharField(max_length=10, choices=TYPE_CHOICES)
    module        = models.CharField(max_length=50)
    reference_id  = models.IntegerField()
    montant       = models.DecimalField(max_digits=12, decimal_places=2)
    description   = models.TextField(blank=True)
