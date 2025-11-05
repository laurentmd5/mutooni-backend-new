from .models import Transaction

def log_transaction(user, type, module, reference_id, montant, description):
    """Crée une entrée d'audit dans Transaction."""
    return Transaction.objects.create(
        type=type,
        module=module,
        reference_id=reference_id,
        montant=montant,
        description=f"{description} (par {user.username if user else 'system'})"
    )
