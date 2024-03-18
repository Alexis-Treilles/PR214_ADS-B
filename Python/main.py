import pyModeS as pms
import datetime 
import time
from fonctions import convert_and_store_trames,lire_colonne_csv,analyse_trames

"""
hex_strings=convert_and_store_trames(trames_value)
df_binary_hex_modified = pd.DataFrame({
    'Binary': trames_value,
    'Hexadecimal': hex_strings
})

# Sauvegarder le DataFrame modifié en fichier CSV
csv_binary_hex_modified_file_path = './binary_hex_trames_modified.csv'
df_binary_hex_modified.to_csv(csv_binary_hex_modified_file_path, index=False)
print(csv_binary_hex_modified_file_path)
"""

hex_strings=lire_colonne_csv("./binary_hex_trames_modified.csv","Hexadecimal")
analyse_trames(hex_strings)