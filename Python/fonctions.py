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

def send_data(info):#envoie des données sur la base de donnée et tri des donnés obsolettes
    print("send_data")
    existing_data = ref.get()
    max_timestamps = {}

    if existing_data:
        for key, value in existing_data.items():
            if 'icao' in value:
                icao = value['icao']
                if icao == info['icao'] and value['latitude'] == info['latitude'] and value['longitude'] == info['longitude']:
                    print("ICAO avec pos identique déjà présent dans la base de données, suppression de l'ancienne valeur...")
                    ref.child(key).delete()
                
                # Mise à jour du timestamp maximum pour chaque ICAO
                if 'timestamp' in value:
                    if icao not in max_timestamps or value['timestamp'] > max_timestamps[icao]:
                        max_timestamps[icao] = value['timestamp']
        
        # Après avoir trouvé le timestamp max pour chaque ICAO, on compare avec le temps actuel
        current_time = get_ntp_time()
        for key, value in existing_data.items():
            if 'icao' in value and 'timestamp' in value:
                icao = value['icao']
                if current_time - max_timestamps[icao] > 10:  # Plus de 10 secondes
                    print(f"Suppression de l'entrée obsolète pour {icao} datant de plus de 10 secondes.")
                    #ref.child(key).delete()             
    ref.push(info)
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
def decode_adsb(message,informations_par_icao):# decode d'une trame hexadécimale
    df = pms.df(message)  # Détecter le type de trame
    icao_id = pms.adsb.icao(message)
    if df == 17 or df == 18:  # Trames de type ADS-B
        tc = pms.adsb.typecode(message)
        print("Type code :",tc)
        time.sleep(1)
        
        if icao_id not in informations_par_icao:
                    
                    informations_par_icao[icao_id] = [icao_id, None, None, None, None, None, None, None]
        heure_actuelle = get_ntp_time()
        #heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")
        informations_par_icao[icao_id][1]=heure_actuelle        
        if 1 <= tc <= 4:  # Identification
            ca = pms.adsb.category(message)
            print("CA : ",ca)
            informations_par_icao[icao_id][2]=categories_aeronefs.get((tc, ca), "Non spécifié")
            callsign = pms.adsb.callsign(message)
            informations_par_icao[icao_id][3] = callsign
        elif 5 <= tc <=18:  # Position superficielle
            if icao_id not in msg_even:
                if icao_id not in msg_odd:
                    msg_even[icao_id]=None
                    msg_odd[icao_id]=None
            trame_bin = bin(int(message, 16))[2:].zfill(len(message)*4)
            bit_54 = trame_bin[53]
            if msg_even[icao_id] == None and bit_54=='0':
                msg_even[icao_id]=message
                t_even[icao_id]=heure_actuelle
            elif  msg_even[icao_id] != None and message!=msg_even[icao_id] and bit_54=='1':
                msg_odd[icao_id]=message
                t_odd[icao_id]=heure_actuelle
            
            if msg_even[icao_id]!=None and msg_odd[icao_id]!=None:
                print("calcul de la position", msg_even[icao_id],msg_odd[icao_id])
                lat, lon = pms.adsb.position(msg_even[icao_id],msg_odd[icao_id] , t_even[icao_id], t_odd[icao_id])
                msg_even[icao_id], msg_odd[icao_id]=None, None
                informations_par_icao[icao_id][4] = lat
                informations_par_icao[icao_id][5] = lon
            
        elif tc == 19 :  # Vitesse
            velocity, heading, vert_rate, _ = pms.adsb.velocity(message)
            informations_par_icao[icao_id][6] = velocity
            informations_par_icao[icao_id][7] = int(heading*360/1024)
            print("heading :", heading,"icao : ",informations_par_icao[icao_id][0])
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
    for hex_string in trames_hexa:
        #print(hex_string)
        decoded_info=decode_adsb(hex_string,informations_par_icao)
        
        if decoded_info != "Type inconnu":
            if decoded_info[4]!=None :
                icao_id = decoded_info[0]
                print(f"Informations pour {icao_id}: {decoded_info}")
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
                    # Vérifier si la valeur d'ICAO existe déjà dans la base de données
                send_data(info)
            
        else:
            print("Type de Trame inconnu")
        message_hexa=""
        hex_list=[]
