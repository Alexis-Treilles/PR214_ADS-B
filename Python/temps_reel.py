import socket
import time
import csv
from fonctions import decode_adsb, send_data
import pyModeS as pms

def main():
    #delete_database()
    informations_par_icao = {}
    
    # Initialiser un compteur pour les trames réussissant le CRC
    crc_pass_count = 0
    
    # Initialiser un compteur pour les informations poussées dans la base de données
    data_push_count = 0
    
    # Nom du fichier CSV où enregistrer les trames valides
    csv_file_name = "trames_valides.csv"

    HOST = 'localhost'  # L'adresse de l'hôte qui exécute ADSB#
    PORT = 47806  # Le port utilisé par ADSB# pour le flux de données

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s, open(csv_file_name, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Timestamp', 'Trame Hexa'])  # En-tête du fichier CSV
        
        s.connect((HOST, PORT))
        print("Connexion établie avec le flux ADSB#.")
        while True:
            raw_data = s.recv(1024)  # Recevoir les données du flux. Ajustez la taille si nécessaire.
            
            #print(raw_data)
            if not raw_data:
                print("Aucune donnée reçue. Tentative de reconnexion...")
                continue

            hex_string = raw_data.decode('utf-8').strip()
            if len(hex_string) == 30:
                
                cleaned_hex_string = hex_string.lstrip('*').rstrip(';')
                df = pms.df(cleaned_hex_string)
                print("trames push :",crc_pass_count,"DF :",df)
                if df in [17, 18]:  # Trames de type ADS-B
                    crc_pass_count += 1  # Incrémenter le compteur de CRC réussis
                    current_timestamp = time.time()
                    # Enregistrer le timestamp et la trame dans le fichier CSV
                    csv_writer.writerow([current_timestamp, cleaned_hex_string])
                    
                    decoded_info = decode_adsb(cleaned_hex_string, informations_par_icao, current_timestamp)
                    if decoded_info != "Type inconnu":
                        icao_id = decoded_info[0]
                        # Vérifiez que vous avez une latitude et une longitude
                        if decoded_info[4] is not None and decoded_info[5] is not None:
                            info = {
                                'icao': decoded_info[0],
                                'timestamp': decoded_info[1],
                                'aircraft_type': decoded_info[2],
                                'callsign': decoded_info[3],
                                'latitude': decoded_info[4],
                                'longitude': decoded_info[5],
                                'velocity': decoded_info[6],
                                'heading': decoded_info[7]
                            }
                            
                            if icao_id not in informations_par_icao:
                                informations_par_icao[icao_id] = info
                            send_data(info)
                            data_push_count += 1  # Incrémenter seulement lorsqu'on pousse de nouvelles informations
                            
                    print(f"Nombre total d'informations poussées dans la base de données : {data_push_count}")

if __name__ == "__main__":
    main()
