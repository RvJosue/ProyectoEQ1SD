import socket
import json
import threading
import time


tracker_data = {
    "seeders": [],
    "leechers": []
}


MAX_HEARTBEAT_INTERVAL = 10

def add_seeder(seeder_ip, seeder_port, shared_files):
    tracker_data["seeders"].append({
        "seeder_ip": seeder_ip,
        "seeder_port": seeder_port,
        "shared_files": shared_files,
        "last_heartbeat": time.time() 
    })

def add_leecher(leecher_ip, leecher_port, file_name):
    tracker_data["leechers"].append({
        "leecher_ip": leecher_ip,
        "leecher_port": leecher_port,
        "file_name": file_name,
        "last_heartbeat": time.time()  
    })

def show_seeders():
    print("\nSeeders conectados:")
    current_time = time.time()

    for seeder in tracker_data["seeders"]:
        last_heartbeat_time = seeder["last_heartbeat"]
        if current_time - last_heartbeat_time <= MAX_HEARTBEAT_INTERVAL:
            print(f"Seeder IP: {seeder['seeder_ip']} Puerto: {seeder['seeder_port']} comparte:")
            for file_id, file_info in seeder['shared_files'].items():
                print(f"  {file_id}. {file_info['file_name']} {file_info['percentage']:.2f}%")
        else:
            print(f"Seeder IP: {seeder['seeder_ip']} Puerto: {seeder['seeder_port']} (Desconectado)")

def show_leechers():
    print("\nLeechers conectados:")
    current_time = time.time()

    for leecher in tracker_data["leechers"]:
        last_heartbeat_time = leecher["last_heartbeat"]
        if current_time - last_heartbeat_time <= MAX_HEARTBEAT_INTERVAL:
            print(f"Leecher IP: {leecher['leecher_ip']} Puerto: {leecher['leecher_port']} desea descargar:")
            print(f"  {leecher['file_name']}")
        else:
            print(f"Leecher IP: {leecher['leecher_ip']} Puerto: {leecher['leecher_port']} (Desconectado)")

def process_heartbeat(data):
    ip = data.get("ip")
    port = data.get("port")
    current_time = time.time()

    for seeder in tracker_data["seeders"]:
        if seeder["seeder_ip"] == ip and seeder["seeder_port"] == port:
            seeder["last_heartbeat"] = current_time
            return

    for leecher in tracker_data["leechers"]:
        if leecher["leecher_ip"] == ip and leecher["leecher_port"] == port:
            leecher["last_heartbeat"] = current_time
            return

def announce_to_tracker_periodically(tracker_host, tracker_port):
    while True:
        time.sleep(5)

        show_seeders()
        show_leechers()

def listen_for_connections(tracker_host, tracker_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((tracker_host, tracker_port))
    server_socket.listen(5)

    print(f"Tracker escuchando en {tracker_host}:{tracker_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexión establecida desde {addr}")

        data = json.loads(client_socket.recv(1024).decode())

        if data["action"] == "announce_seeder":
            add_seeder(data['seeder_ip'], data['seeder_port'], data['shared_files'])
        elif data["action"] == "announce_leecher":
            add_leecher(data['leecher_ip'], data['leecher_port'], data['file_name'])
        elif data["action"] == "heartbeat":
            process_heartbeat(data)

        show_seeders()
        show_leechers()

        print(f"Enviando al cliente: {json.dumps(tracker_data)}")
        client_socket.send(json.dumps(tracker_data).encode())

        client_socket.close()

if __name__ == "__main__":
    tracker_host = input("Ingrese la IP del tracker: ")
    tracker_port = int(input("Ingrese el puerto del tracker: "))

    threading.Thread(target=announce_to_tracker_periodically, args=(tracker_host, tracker_port), daemon=True).start()
    listen_for_connections(tracker_host, tracker_port)
