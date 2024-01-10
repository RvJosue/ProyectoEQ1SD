import socket
import os
import json
import threading
import time 

def check_and_send_files():
    torrents_folder = "Torrents"
    available_files = []

    torrent_files = [file for file in os.listdir(torrents_folder) if file.endswith('.torrent')]

    for torrent_file in torrent_files:
        with open(os.path.join(torrents_folder, torrent_file), 'r') as torrent:
            try:
                torrent_data = json.load(torrent)

                file_name = torrent_data["name"]
                total_pieces = torrent_data["pieces"]
                file_extension = file_name.split('.')[-1]  
                file_folder = f"{file_name}_pieces" 
                file_folder_path = os.path.join(file_folder)

                print(f"Checking File: {file_name}, Total Pieces: {total_pieces}, Folder Path: {file_folder_path}")

                if os.path.exists(file_folder_path):
                    existing_pieces = len([f for f in os.listdir(file_folder_path) if f.endswith('.dat')])
                    percentage = (existing_pieces / total_pieces) * 100

                    if percentage > 20:
                        available_files.append((file_name, percentage))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {torrent_file}: {e}")

    if available_files:
        print("Available Files:")
        for file, percentage in available_files:
            print(f"{file} - {percentage:.2f}%")
    else:
        print("No hay archivos disponibles para transferir.")

    return available_files


def receive_and_save_file_pieces(client_socket, file_name):
    total_pieces = int(client_socket.recv(1024).decode())
    print(f"Recibiendo {total_pieces} piezas...")

    base_name, extension = os.path.splitext(file_name)
    folder_name = f"{base_name}{extension}_pieces"
    os.makedirs(folder_name, exist_ok=True)

    for piece_number in range(1, total_pieces + 1):
        piece_path = os.path.join(folder_name, f"piece_{piece_number}.dat")
        with open(piece_path, 'wb') as piece_file:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                piece_file.write(data)
                if len(data) < 1024:
                    break 

            client_socket.send(b'1') 

    print(f"Las piezas fueron recibidas y guardadas en '{folder_name}'")

def get_tracker_info(torrent_file):
    with open(torrent_file, 'r') as torrent:
        try:
            torrent_data = json.load(torrent)
            file_name = torrent_data["name"]
            tracker_ip = torrent_data["tracker"]
            tracker_port = torrent_data["puertoTracker"]
            return file_name, tracker_ip, tracker_port
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {torrent_file}: {e}")
            return None, None, None
        

def connect_to_tracker_heartbeat(tracker_ip, tracker_port, seeder_port):
    while True:
        time.sleep(5) 


        heartbeat_data = {
            "action": "heartbeat",
            "ip": socket.gethostbyname(socket.gethostname()),
            "port": seeder_port
        }

        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tracker_socket.connect((tracker_ip, tracker_port))
            tracker_socket.send(json.dumps(heartbeat_data).encode())
        except Exception as e:
            print(f"Error al enviar heartbeat al tracker: {e}")
        finally:
            tracker_socket.close()

def heartbeat_to_tracker(tracker_ip, tracker_port, leecher_port):
    while True:
        time.sleep(5)  

        heartbeat_data = {
            "action": "heartbeat",
            "ip": socket.gethostbyname(socket.gethostname()),
            "port": leecher_port
        }

        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tracker_socket.connect((tracker_ip, tracker_port))
            tracker_socket.send(json.dumps(heartbeat_data).encode())
        except Exception as e:
            print(f"Error al enviar heartbeat al tracker: {e}")
        finally:
            tracker_socket.close()

def connect_to_seeder(file_name, seeder_ip, seeder_port):

    leecher_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    leecher_socket.connect((seeder_ip, seeder_port))

    leecher_ip, leecher_port = leecher_socket.getsockname()
    print(f"Conectado al seeder desde {leecher_ip}:{leecher_port}")

    leecher_socket.send(file_name.encode())
    receive_and_save_file_pieces(leecher_socket, file_name)

    leecher_socket.close()
    
        
def start_client():
    seeders = []
    connected_to_seeder = False
    torrents_folder = "Torrents"
    available_files = []

    torrent_files = [file for file in os.listdir(torrents_folder) if file.endswith('.torrent')]

    for i, torrent_file in enumerate(torrent_files, start=1):
        file_name, tracker_ip, tracker_port = get_tracker_info(os.path.join(torrents_folder, torrent_file))
        if file_name and tracker_ip and tracker_port:
            print(f"{i}. Archivo: {file_name}, Tracker IP: {tracker_ip}, Tracker Port: {tracker_port}")

    selected_index = int(input("Seleccione el número del archivo que desea descargar: ")) - 1
    selected_torrent_file = os.path.join(torrents_folder, torrent_files[selected_index])
    file_name, tracker_ip, tracker_port = get_tracker_info(selected_torrent_file)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((tracker_ip, tracker_port))

    client_ip, client_port = client_socket.getsockname()
    print(f"Conectado al tracker desde {client_ip}:{client_port}")

    request_data = {
        "action": "announce_leecher",
        "leecher_ip": client_ip,
        "leecher_port": client_port,
        "file_name": file_name,
    }

    client_socket.send(json.dumps(request_data).encode())

    response = client_socket.recv(1024).decode()
    print(f"Respuesta del tracker: {response}")

    try:
        tracker_info = json.loads(response)
        seeders = tracker_info.get("seeders", [])
        leechers = tracker_info.get("leechers", [])

        if seeders and not connected_to_seeder:  
            seeder_info = seeders[0] 
            seeder_ip = seeder_info.get("seeder_ip")
            seeder_port = seeder_info.get("seeder_port")

            if seeder_ip and seeder_port:

                connect_to_seeder(file_name, seeder_ip, seeder_port)
                connected_to_seeder = True 
            else:
                print("La respuesta del tracker no contiene la información esperada.")
        elif not seeders:
            print("No hay seeders disponibles en la respuesta del tracker.")
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error decoding or processing tracker response: {e}")
    client_socket.close()

def create_pieces_folder(file_path):
    folder_name = f"{os.path.splitext(os.path.basename(file_path))[0]}.{os.path.splitext(os.path.basename(file_path))[1][1:]}_pieces"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def send_file_pieces(conn, folder_path):
    pieces = [f for f in os.listdir(folder_path) if f.endswith('.dat')]
    pieces.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

    total_pieces = len(pieces)
    conn.send(str(total_pieces).encode())

    for piece in pieces:
        piece_path = os.path.join(folder_path, piece)
        with open(piece_path, 'rb') as piece_file:
            while True:
                data = piece_file.read(1024)
                if not data:
                    break
                conn.send(data)
                conn.recv(1) 

def write_tracker_info(available_files, tracker_host, tracker_port, seeder_port):
    tracker_data = {
        "action": "announce_seeder", 
        "seeder_ip": socket.gethostbyname(socket.gethostname()),  
        "seeder_port": seeder_port, 
        "shared_files": {}
    }

    for i, (file_name, percentage) in enumerate(available_files, start=1):
        tracker_data["shared_files"][i] = {
            "file_name": file_name,
            "percentage": percentage,
        }

    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker_socket.connect((tracker_host, tracker_port))
    tracker_socket.send(json.dumps(tracker_data).encode())
    tracker_socket.close()




def start_server(available_files, tracker_host, tracker_port):
    if not available_files:
        print("No hay archivos disponibles para transferir.")
        return

    print("Archivos disponibles para transferir:")
    for i, (file_name, percentage) in enumerate(available_files, start=1):
        print(f"{i}. {file_name} {percentage:.2f}% se puede transferir")

    host = input("Ingrese la IP del servidor: ")
    port = int(input("Ingrese el puerto del servidor: "))

    write_tracker_info(available_files, tracker_host, tracker_port, port)


    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Servidor escuchando en {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Conexión establecida desde {addr}")

        client_ip, client_port = conn.getpeername()
        print(f"Cliente: {client_ip}:{client_port}")

        file_name = conn.recv(1024).decode() + "_pieces"

        send_file_pieces(conn, file_name)

        print(f"Las piezas del archivo '{file_name}' fueron enviadas con éxito")

        conn.close()


def main():
    print("Seleccione el modo:")
    print("1. Leecher")
    print("2. Seeder")

    mode = input("Ingrese el número del modo: ")

    if mode == "1":
        
        
        tracker_host = input("Ingrese la IP del tracker: ")
        tracker_port = int(input("Ingrese el puerto del tracker: "))
        
        leecher_port = int(input("Ingrese el puerto del leecher: "))

        threading.Thread(target=heartbeat_to_tracker, args=(tracker_host, tracker_port, leecher_port), daemon=True).start()
        start_client()
    elif mode == "2":
        available_files = check_and_send_files()
        
        tracker_host = input("Ingrese la IP del tracker: ")
        tracker_port = int(input("Ingrese el puerto del tracker: "))

        seeder_port = int(input("Ingrese el puerto del seeder proporcionado por el tracker: "))

        threading.Thread(target=connect_to_tracker_heartbeat, args=(tracker_host, tracker_port, seeder_port), daemon=True).start()
        start_server(available_files, tracker_host, tracker_port)
    else:
        print("Modo no válido. Por favor, seleccione 1 o 2.")

if __name__ == "__main__":
    main()