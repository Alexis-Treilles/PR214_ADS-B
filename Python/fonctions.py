import pyModeS as pms
import datetime 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate('cred.json') 
import socket
import struct
import time
import pandas as pd
firebase_admin.initialize_app(cred,{'databaseURL' : 'https://test-349ac-default-rtdb.europe-west1.firebasedatabase.app/'})
ref = db.reference('/')
msg_odd= {}
msg_even = {}
t_even={}
t_odd={}
categories_aeronefs = {
    (1, 0): "No category information",
    (2, 0): "No category information",
    (3, 0): "No category information",
    (4, 0): "No category information",
    (2, 1): "Surface emergency vehicle",
    (2, 3): "Surface service vehicle",
    (2, range(4, 8)): "Ground obstruction",
    (3, 1): "Glider or sailplane",
    (3, 2): "Lighter-than-air",
    (3, 3): "Parachutist or skydiver",
    (3, 4): "Ultralight, hang-glider, or paraglider",
    (3, 6): "Unmanned aerial vehicle",
    (3, 7): "Space or transatmospheric vehicle",
    (4, 1): "Light aircraft (less than 7000 kg)",
    (4, 2): "Medium aircraft 1 (7000 kg to 34000 kg)",
    (4, 3): "Medium aircraft 2 (34000 kg to 136000 kg)",
    (4, 4): "High vortex aircraft",
    (4, 5): "Heavy aircraft (larger than 136000 kg)",
    (4, 6): "High performance aircraft",
    (4, 7): "Rotorcraft",
    # Continuer avec les autres combinaisons de TC et CA...
}



data_push_count = 0
def send_data(info):  # envoie des données sur la base de donnée ( Firebase)
    
    existing_data = ref.get()
    new_data_timestamp = info['timestamp']
    icao = info['icao']
    latitude = info['latitude']
    longitude = info['longitude']

    if existing_data:
        data_to_delete = []
        for key, value in existing_data.items():
            # Vérification de l'existence de 'icao', 'latitude', et 'longitude' avant de continuer
            if all(k in value for k in ['icao', 'latitude', 'longitude']):
                existing_icao = value['icao']
                existing_latitude = value['latitude']
                existing_longitude = value['longitude']
                existing_timestamp = value['timestamp']
                
                
                if icao == existing_icao and latitude == existing_latitude and longitude == existing_longitude:
                   
                    if new_data_timestamp - existing_timestamp > 600: 
                        data_to_delete.append(key)
                    
                  
                
        # Supprimer les données obsolètes
        for key in data_to_delete:
            ref.child(key).delete()
    supprimer_points_avions()

    
    # Ajouter la nouvelle donnée à la base de données
    ref.push(info)
    print("push")
           
     
         
    
def get_ntp_time(host="time.google.com"):
    port = 123
    buffer = 1024
    address = (host, port)
    
    # Créer un message NTP (voir RFC 4330 pour les détails)
    msg = b'\x1b' + 47 * b'\0'
    
    # envoie du message NTP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(4)
        sock.sendto(msg, address)
        
        # Recevoir la réponse et extraire le timestamp
        msg, address = sock.recvfrom(buffer)
        
    # Le temps est dans les octets 40 à 43 est un entier représentant le nombre de secondes depuis le 1er janvier 1900
    
    t = struct.unpack('!12I', msg)[10]
    t -= 2208988800  # Convertir le temps NTP en temps Unix
    
    return t 
def decode_adsb(message, informations_par_icao, timestamp):  # decode d'une trame hexadécimale
    df = pms.df(message)  
    print("df:",df)
    latitude_ref = 44.78704750094399 
    longitude_ref = -0.6058691316266133  

    if df in [17, 18]:  # Trames de type ADS-B
        icao_id = pms.adsb.icao(message)
        tc = pms.adsb.typecode(message)
        
        if icao_id not in informations_par_icao:
            informations_par_icao[icao_id] = [icao_id, None, None, None, None, None, None, None]
        
        informations_par_icao[icao_id][1] = timestamp  
        
        if 1 <= tc <= 4:  # Identification
            ca = pms.adsb.category(message)
            informations_par_icao[icao_id][2] = categories_aeronefs.get((tc, ca), "Non spécifié")
            callsign = pms.adsb.callsign(message)
            informations_par_icao[icao_id][3] = callsign
       
        if tc in range(5, 19):
            # Calculer la position à partir d'un seul message en utilisant une position de référence
            lat, lon = pms.adsb.position_with_ref(message, latitude_ref, longitude_ref)
            
            # mettre à jour les informations associées à l'identifiant ICAO
            informations_par_icao[icao_id][4] = lat
            informations_par_icao[icao_id][5] = lon
        elif tc == 19:  # Vitesse
            velocity, heading, vert_rate, _ = pms.adsb.velocity(message)
            informations_par_icao[icao_id][6] = velocity
            informations_par_icao[icao_id][7] = int(heading * 360 / 1024 + 35)
        return informations_par_icao[icao_id]
    else:
        return "Type inconnu"
def convert_and_store_trames(binary_trames):
    
    hex_strings = []
    
    for binary_trame in binary_trames:
        # Convertir la trame binaire en entier, puis en chaîne hexadécimale, et la mettre en majuscules
        hex_string = hex(int(binary_trame, 2))[2:].upper().zfill(len(binary_trame) // 4)
        
        hex_strings.append(hex_string)
    return hex_strings
def lire_colonne_csv(nom_fichier, nom_colonne):# lecture du csv et extraction d'une liste de trame hexa
    
    df = pd.read_csv(nom_fichier)
    
    # Vérification si la colonne existe
    if nom_colonne not in df.columns:
        print(f"La colonne '{nom_colonne}' n'existe pas dans le fichier CSV.")
        return None
    
    # Extraction
    colonne = df[nom_colonne].tolist()
    
    return colonne


def analyse_trames_progress(trames_hexa, echs):
    total_trames = len(trames_hexa)
    trames_traitees = 0
    start_time = time.time()
    informations_par_icao = {}
    icao_uniques = set()
    
    #timestamps = [ech / 4000000 for ech in echs]
    timestamps=echs
    for index, hex_string in enumerate(trames_hexa):
        current_timestamp = timestamps[index]+get_ntp_time()
        
        decoded_info = decode_adsb(hex_string, informations_par_icao, current_timestamp)
        
        if decoded_info != "Type inconnu":
            if decoded_info[4] != None: 
                icao_id = decoded_info[0]
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
                    
                if icao_id not in icao_uniques:
                    icao_uniques.add(icao_id)
                send_data(info)
        
        trames_traitees += 1
        if index < total_trames - 1:
            # Calcul de la différence de temps entre la trame actuelle et la suivante
            next_timestamp = timestamps[index + 1]
            delay = next_timestamp - current_timestamp
          
        
        # Mise à jour de la barre de progression
        progress = (trames_traitees / total_trames) * 100
        elapsed_time = time.time() - start_time
        bar_length = 100
        progress_chars = int(bar_length * (progress / 100))
        bar = '[' + '#' * progress_chars + ' ' * (bar_length - progress_chars) + ']'
        print(f"\rProgression : {bar} {progress:.2f}% Temps écoulé : {elapsed_time:.2f} secondes", end='', flush=True)

def supprimer_points_avions():
    existing_data = ref.get()
    if existing_data:
        points_supprimes = 0
        for key, value in existing_data.items():
            if 'timestamp' in value:
                timestamp = value['timestamp']
                current_time = int(time.time())
                if current_time - timestamp > 300:  # 5 minutes en secondes
                    ref.child(key).delete()
                    points_supprimes += 1
                    print(f"Point d'avion supprimé pour la clé {key}")
        print(f"Total des points d'avions supprimés : {points_supprimes}")