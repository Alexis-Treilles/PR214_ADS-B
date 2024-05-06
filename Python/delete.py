import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Chemin vers votre fichier de clé de service Firebase
cred_path = 'cred.json'

# Initialiser l'application Firebase avec vos credentials et l'URL de votre base de données
cred = credentials.Certificate('Python/cred.json')
firebase_admin.initialize_app(cred,{'databaseURL' : 'https://test-349ac-default-rtdb.europe-west1.firebasedatabase.app/'})
ref = db.reference('/')

# Référence à la racine de votre base de données
root_ref = db.reference('/')

# Supprimer toutes les données à la racine de la base de données
root_ref.delete()

print("Toutes les données ont été supprimées de la base de données.")
