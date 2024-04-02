import pandas as pd
import pyModeS as pms

def add_parity_to_same_csv(file_path):
    # Lire le fichier CSV
    df = pd.read_csv(file_path)
    
    # Calculer les bits de parité pour chaque trame et les concaténer avec la trame originale
    df['Hexadecimal'] = df['Hexadecimal_sans_p'].apply(lambda x: x + format(pms.crc(x, encode=True), '06X'))
    
    # Réécrire le DataFrame modifié dans le même fichier CSV
    df.to_csv(file_path, index=False)

# Exemple d'utilisation
file_path = './frames (1).csv'
add_parity_to_same_csv(file_path)




import pandas as pd

def convert_and_fix_hex_in_csv(csv_file_path):
    # Lire le fichier CSV
    df = pd.read_csv(csv_file_path)
    
    # Fonction pour convertir une chaîne hexadécimale en binaire, inverser les bits, puis reconvertir en hexadécimal
    def fix_hex(hex_inv):
        # Convertir l'hexadécimal en binaire
        bin_str = bin(int(hex_inv, 16))[2:].zfill(8 * ((len(hex_inv) + 1) // 2))
        # Inverser l'ordre des bits
        bin_str_reversed = bin_str[::-1]
        # Reconvertir en hexadécimal
        hex_corrected = hex(int(bin_str_reversed, 2))[2:].zfill(len(hex_inv))
        hex_inv_reversed = hex_corrected[::-1]
        return bin_str_reversed, hex_inv_reversed

    # Appliquer la fonction de correction à chaque entrée de la colonne 'Hexadecimal_inv'
    df['binary'], df['Hexadecimal'] = zip(*df['Hexadecimal_inv'].apply(fix_hex))
    
    # Écrire le DataFrame corrigé dans le même fichier CSV
    df.to_csv(csv_file_path, index=False)

# Utilisation de la fonction avec le chemin vers votre fichier CSV
file_path = './log_prof.csv'
#convert_and_fix_hex_in_csv(file_path)
