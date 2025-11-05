from . import schema_extensions

"""
Module principal de l'application 'core' pour Mutooni ERP.

Ce package contient :
- Les modèles métiers (stock, vente, achat, RH, transaction)
- Les vues DRF associées
- Les serializers par domaine
- La logique d’authentification Firebase
- Un logger d’audit des transactions
- L’initialisation Firebase Admin
"""

default_app_config = "core.apps.CoreConfig"
