import pyModeS as pms
import datetime 
import time
from fonctions import lire_colonne_csv,analyse_trames_progress
def main():
    
    while True:
        # Lire et traiter le premier fichier CSV
        hex_strings = lire_colonne_csv("CSV/log_prof.csv", "Hexadecimal")
        echs = lire_colonne_csv("CSV/log_prof.csv   ", "ech")
        analyse_trames_progress(hex_strings, echs)

     
        time.sleep(5)

if __name__ == "__main__":
    main()