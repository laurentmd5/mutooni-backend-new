from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Modules métiers ERP'

    def ready(self):
        # Import ici les signaux ou autres initialisations au démarrage de l'app si nécessaire
        try:
            import core.signals  # si tu en ajoutes plus tard
            logger.info("Signaux core chargés.")
        except ImportError:
            logger.info("Aucun signal trouvé dans core.")
