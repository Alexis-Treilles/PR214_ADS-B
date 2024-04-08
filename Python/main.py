import pyModeS as pms
import datetime 
import time
from fonctions import convert_and_store_trames,lire_colonne_csv,analyse_trames,analyse_trames_progress,delete_database
def main():
    delete_database()
    while True:
        # Lire et traiter le premier fichier CSV
        hex_strings = lire_colonne_csv("log_prof.csv", "Hexadecimal")
        echs = lire_colonne_csv("log_prof.csv", "ech")
        analyse_trames_progress(hex_strings, echs)

        # Lire et traiter le deuxième fichier CSV
        hex_strings = lire_colonne_csv("frames (1).csv", "Hexadecimal")
        echs = lire_colonne_csv("frames (1).csv", "Temps")
        #analyse_trames_progress(hex_strings, echs)

        # Supprimer la base de données une fois que tous les fichiers ont été lus
        delete_database()

        # Pause de 5 secondes avant de recommencer la boucle
        time.sleep(5)

if __name__ == "__main__":
    main()