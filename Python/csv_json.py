import csv
import json

# Chemin d'accès au fichier CSV d'entrée
input_csv_file = 'PR214/CSV/airports.csv'

# Chemin d'accès au fichier JSON de sortie
output_json_file = 'PR214/JSON/aeroports.json'

# Lire le fichier CSV et écrire le fichier JSON
with open(input_csv_file, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    data = [row for row in csv_reader]

with open(output_json_file, mode='w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

print("La conversion du fichier CSV en JSON a réussi.")