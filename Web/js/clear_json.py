import json

# Chemin du fichier JSON d'entrée
input_file_path = 'Web/json/airports.json'

# Chemin du fichier JSON de sortie
output_file_path = 'Web/european_airports.json'

# Fonction pour charger les données du fichier JSON
def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

# Fonction pour sauvegarder les données dans un fichier JSON
def save_data(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

# Charger les données aéroportuaires
data = load_data(input_file_path)

# Liste pour stocker les aéroports européens
european_airports = []

# Boucle pour filtrer les aéroports européens
for airport in data:
    if 'Europe' in airport['tz'] and airport['type'] == "Airports":
        european_airports.append(airport)

# Sauvegarder les données filtrées
save_data(european_airports, output_file_path)

print(f"Fichier '{output_file_path}' créé avec les données des aéroports européens.")
