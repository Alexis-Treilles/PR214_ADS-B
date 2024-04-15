import socket

def read_adsb_data(host='127.0.0.1', port=47806):
    # Créer un socket TCP/IP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Se connecter au serveur ADSB#
    server_address = (host, port)
    print(f"Connexion à {server_address}")
    sock.connect(server_address)
    
    try:
        # Recevoir et afficher les données en continu
        while True:
            data = sock.recv(1024)  # Taille du buffer à 1024 bytes
            if data:
                # Traitement des données reçues
                print("Données reçues:", data)
            else:
                # Pas de données, fermer la connexion
                break
    finally:
        sock.close()

if __name__ == '__main__':
    read_adsb_data()
