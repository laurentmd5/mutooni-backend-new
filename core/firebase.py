import os
from firebase_admin import credentials, initialize_app
from django.conf import settings

# Deux emplacements possibles (local/dev et conteneur)
cred_paths = [
    os.path.join(settings.BASE_DIR, 'firebase', 'serviceAccountKey.json'),  # Pour le conteneur
    os.path.join(settings.BASE_DIR, 'core', 'firebase', 'serviceAccountKey.json')  # Pour le dev local
]

cred_path = None
for path in cred_paths:
    if os.path.exists(path):
        cred_path = path
        break

if not cred_path:
    raise FileNotFoundError(f"""
    Fichier Firebase introuvable. Cherché aux emplacements:
    - {cred_paths[0]}
    - {cred_paths[1]}
    """)

cred = credentials.Certificate(cred_path)
firebase_app = initialize_app(cred)