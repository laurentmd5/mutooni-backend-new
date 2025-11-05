from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    - Ajoute un champ 'role' pour la gestion des ACL.
    """
    ROLE_ADMIN   = "admin"
    ROLE_VENDOR  = "vendor"
    ROLE_STAFF   = "staff"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_VENDOR, "Vendor"),
        (ROLE_STAFF, "Staff"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAFF,
        help_text="Rôle métier de l'utilisateur"
    )

    def __str__(self):
        return self.username
