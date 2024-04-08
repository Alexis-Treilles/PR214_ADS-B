import pyModeS as pms
import datetime 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate('PR214/cred.json') 
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
def delete_database():
    # Référence à la racine de votre base de données
    root_ref = db.reference('/')
    # Supprimer toutes les données à la racine de la base de données
    root_ref.delete()
    print("Toutes les données ont été supprimées de la base de données.")


data_push_count = 0
def send_data(info):  # envoie des données sur la base de donnée et tri des données obsolettes
    
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
                
                # Si les coordonnées et l'ICAO correspondent à celles fournies dans la nouvelle donnée
                if icao == existing_icao and latitude == existing_latitude and longitude == existing_longitude:
                    # Comparer le timestamp de la nouvelle donnée avec celui de l'entrée existante
                    if new_data_timestamp - existing_timestamp > 600:  # Supprimer si la différence de timestamp est supérieure à 30 secondes
                        data_to_delete.append(key)
                        #print("suppr")
                    else:
                        # Ne pas ajouter la nouvelle donnée si elle correspond déjà à une entrée existante
                         return
                
        # Supprimer les données obsolètes
        for key in data_to_delete:
            ref.child(key).delete()
    
    # Ajouter la nouvelle donnée à la base de données
    ref.push(info)
    print("push")
           
     
         
    
def get_ntp_time(host="time.google.com"):# temps NTP
    port = 123
    buffer = 1024
    address = (host, port)
    
    # Créer un message NTP (voir RFC 4330 pour les détails)
    msg = b'\x1b' + 47 * b'\0'
    
    # Ouvrir un socket et envoyer le message NTP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(4)
        sock.sendto(msg, address)
        
        # Recevoir la réponse et extraire le timestamp
        msg, address = sock.recvfrom(buffer)
        
    # Le temps est dans les octets 40 à 43 et est un nombre entier représentant
    # le nombre de secondes depuis le 1er janvier 1900
    t = struct.unpack('!12I', msg)[10]
    t -= 2208988800  # Convertir le temps NTP en temps Unix
    
    return t 
def decode_adsb(message, informations_par_icao, timestamp):  # decode d'une trame hexadécimale
    df = pms.df(message)  # Détecter le type de trame
    print("df:",df)
    latitude_ref = 44.78704750094399 
    longitude_ref = -0.6058691316266133  

    if df in [17, 18]:  # Trames de type ADS-B
        icao_id = pms.adsb.icao(message)
        tc = pms.adsb.typecode(message)
        
        if icao_id not in informations_par_icao:
            informations_par_icao[icao_id] = [icao_id, None, None, None, None, None, None, None]
        
        informations_par_icao[icao_id][1] = timestamp  # Utilisation du timestamp pour la date et heure
        
        if 1 <= tc <= 4:  # Identification
            ca = pms.adsb.category(message)
            informations_par_icao[icao_id][2] = categories_aeronefs.get((tc, ca), "Non spécifié")
            callsign = pms.adsb.callsign(message)
            informations_par_icao[icao_id][3] = callsign
        """
        elif 5 <= tc <= 18:  # Position superficielle
            if icao_id not in msg_even:
                msg_even[icao_id] = None
                msg_odd[icao_id] = None
            
            trame_bin = bin(int(message, 16))[2:].zfill(len(message)*4)
            bit_54 = trame_bin[53]
            if msg_even[icao_id] == None and bit_54 == '0':
                msg_even[icao_id] = message
                t_even[icao_id] = timestamp
            elif msg_even[icao_id] != None and message != msg_even[icao_id] and bit_54 == '1':
                msg_odd[icao_id] = message
                t_odd[icao_id] = timestamp
            
            if msg_even[icao_id] != None and msg_odd[icao_id] != None:
                lat, lon = pms.adsb.position(msg_even[icao_id], msg_odd[icao_id], t_even[icao_id], t_odd[icao_id])
                msg_even[icao_id], msg_odd[icao_id] = None, None
                informations_par_icao[icao_id][4] = lat
                informations_par_icao[icao_id][5] = lon
                #print("pos")
            """
        if tc in range(5, 19):
            # Calculer la position à partir d'un seul message en utilisant une position de référence
            lat, lon = pms.adsb.position_with_ref(message, latitude_ref, longitude_ref)
            
            # Vous pouvez ensuite mettre à jour les informations associées à l'identifiant ICAO
            informations_par_icao[icao_id][4] = lat
            informations_par_icao[icao_id][5] = lon
        elif tc == 19:  # Vitesse
            velocity, heading, vert_rate, _ = pms.adsb.velocity(message)
            informations_par_icao[icao_id][6] = velocity
            informations_par_icao[icao_id][7] = int(heading * 360 / 1024 + 35)
        return informations_par_icao[icao_id]
    else:
        return "Type inconnu"
def convert_and_store_trames(binary_trames):# prends les trames binaires, les store en hexa, return liste des trames en hexa
    # Initialiser une liste vide pour stocker les chaînes hexadécimales
    hex_strings = []
    # Parcourir chaque trame binaire
    for binary_trame in binary_trames:
        # Convertir la trame binaire en entier, puis en chaîne hexadécimale, et la mettre en majuscules
        hex_string = hex(int(binary_trame, 2))[2:].upper().zfill(len(binary_trame) // 4)
        # Ajouter la chaîne hexadécimale résultante à la liste
        hex_strings.append(hex_string)
    return hex_strings
def lire_colonne_csv(nom_fichier, nom_colonne):# lecture du csv et extraction d'une liste de trame hexa
    # Lecture du fichier CSV
    df = pd.read_csv(nom_fichier)
    
    # Vérification si la colonne existe
    if nom_colonne not in df.columns:
        print(f"La colonne '{nom_colonne}' n'existe pas dans le fichier CSV.")
        return None
    
    # Extraction de la colonne et stockage dans une variable
    colonne = df[nom_colonne].tolist()
    
    return colonne
def analyse_trames(trames_hexa): # prends les trames en hexa et, decode, écris et trie la base de donnée
    informations_par_icao = {}
    # Initialiser l'application Firebase
    hex_strings=[]
    message_hexa=""
    icao_uniques = set()  # Ensemble pour conserver les ICAO uniques
    for hex_string in trames_hexa:
        #print(hex_string)
        decoded_info=decode_adsb(hex_string,informations_par_icao)
        #print(decoded_info)
        if decoded_info != "Type inconnu":
            #print("decoded info : ",decoded_info)
            #if decoded_info[4]!=None :
                icao_id = decoded_info[0]
                #print(f"Informations pour {icao_id}: {decoded_info}")
                info = {
                'icao': decoded_info[0],
                'timestamp': decoded_info[1],
                'aircraft_type':decoded_info[2],
                'callsign': decoded_info[3],
                'latitude': decoded_info[4],
                'longitude': decoded_info[5],
                'velocity': decoded_info[6],
                'heading': decoded_info[7]
                }
                if icao_id not in icao_uniques:
                    icao_uniques.add(icao_id)
                    # Vérifier si la valeur d'ICAO existe déjà dans la base de données
                #print(info)
                send_data(info)

        
            #print("Type de Trame inconnu")
        message_hexa=""
        hex_list=[]
    #print(icao_uniques)

def analyse_trames_progress(trames_hexa, echs):
    total_trames = len(trames_hexa)
    trames_traitees = 0
    start_time = time.time()
    informations_par_icao = {}
    icao_uniques = set()
    
    # Calcul des timestamps à partir de echs
    timestamps = [ech / 4000000 for ech in echs]
    
    for index, hex_string in enumerate(trames_hexa):
        current_timestamp = timestamps[index]
        
        # Ajout du timestamp à l'appel de la fonction decode_adsb
        decoded_info = decode_adsb(hex_string, informations_par_icao, current_timestamp)
        
        if decoded_info != "Type inconnu":
            if decoded_info[4] != None:  # Si latitude est non None
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
            #time.sleep(delay)  # Attente du délai avant de traiter la trame suivante
        
        # Mise à jour de la barre de progression
        progress = (trames_traitees / total_trames) * 100
        elapsed_time = time.time() - start_time
        bar_length = 100
        progress_chars = int(bar_length * (progress / 100))
        bar = '[' + '#' * progress_chars + ' ' * (bar_length - progress_chars) + ']'
        print(f"\rProgression : {bar} {progress:.2f}% Temps écoulé : {elapsed_time:.2f} secondes", end='', flush=True)

