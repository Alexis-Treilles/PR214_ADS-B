import socket
import threading
import time
import subprocess

class MyServer:
    def __init__(self, host='localhost', port=47806):
        self.host = host
        self.port = port
        self.server_socket = None
        self.stop_server = threading.Event()
        self.client_sockets = []
        self.server_thread = None
        self.process = None

    def open(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Serveur démarré sur {self.host}:{self.port}, en attente de connexions...")
        self.server_thread = threading.Thread(target=self._start_server)
        self.server_thread.start()
        self.process = subprocess.Popen(["python", "./Python/temps_reel.py"])
        threading.Timer(10, self._close_process).start()

    def _start_server(self):
        try:
            while not self.stop_server.is_set():
                print("En attente de connexion client...")
                client_socket, addr = self.server_socket.accept()
                print(f"Connexion établie avec {addr}")
                self.client_sockets.append(client_socket)
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                client_thread.start()
        except Exception as e:
            print(f"Erreur du serveur : {e}")
        finally:
            self.close()

    def _handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print("Réception de la trame :", data.decode())
        except Exception as e:
            print(f"Erreur de réception des données : {e}")
        finally:
            client_socket.close()
            self.client_sockets.remove(client_socket)
            print("Connexion client fermée.")

    def _close_process(self):
        if self.process:
            self.process.terminate()
            print("Processus temps_reel.py fermé.")

    def send(self, hexa_frame):
        formatted_frame = f"*{hexa_frame};"
        for sock in self.client_sockets:
            try:
                sock.sendall(formatted_frame.encode('utf-8'))
                print(f"Trame envoyée: {formatted_frame}")
            except socket.error as e:
                print(f"Erreur lors de l'envoi de la trame : {e}")
                sock.close()
                self.client_sockets.remove(sock)

    def close(self):
        self.stop_server.set()
        for sock in self.client_sockets:
            sock.close()
        if self.server_socket:
            self.server_socket.close()
            print("Serveur fermé.")

if __name__ == "__main__":
    my_server = MyServer()
    my_server.open()

    time.sleep(3)  
    my_server.send("8D40621D58C386435CC412692AD6")
    print("Trame envoyée")

    time.sleep(5)
    my_server.close()
