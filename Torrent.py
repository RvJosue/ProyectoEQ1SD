import json
import hashlib
import os

class Torrent:

    PEDAZO_TAM = 1023  # bytes
    HASH_ALGORITHM = "md5"

    def __init__(self, torrent_path):
        with open(torrent_path, "r") as file:
            data = json.load(file)
            self.id = data["id"]
            self.tracker = data["tracker"]
            self.puertoTracker = data["puertoTracker"]
            self.pedazos = data["pieces"]
            self.ultimo_pedazo = data["lastPiece"]
            self.nombre = data["name"]
            self.archivo = data["filepath"]
            self.checksum = data["checksum"]
        self.obtenidos = [False] * self.pedazos

    def is_piece_valid(self, piece, index):
        m = hashlib.new(self.HASH_ALGORITHM)
        return self.hash(m, piece) == self.checksum[index]

    @staticmethod
    def read_piece(torrent, piece_index):
        with open(torrent.archivo, "rb") as file:
            piece_size = min(Torrent.PEDAZO_TAM, os.path.getsize(torrent.archivo) - piece_index * Torrent.PEDAZO_TAM)
            file.seek(piece_index * Torrent.PEDAZO_TAM)
            piece = file.read(piece_size)
            return piece

    @staticmethod
    def hash(message_digest, data):
        message_digest.update(data)
        digest = message_digest.digest()
        return hashlib.md5(digest).hexdigest()

    @staticmethod
    def split_file(file_path):
        pieces = []
        with open(file_path, "rb") as file:
            while True:
                data = file.read(Torrent.PEDAZO_TAM)
                if not data:
                    break
                pieces.append(data)
        return pieces

    @staticmethod
    def calculate_checksums(file_path):
        checksums = []
        with open(file_path, "rb") as file:
            while True:
                data = file.read(Torrent.PEDAZO_TAM)
                if not data:
                    break
                m = hashlib.new(Torrent.HASH_ALGORITHM)
                checksums.append(Torrent.hash(m, data))
        return checksums

    @staticmethod
    def create_pieces_folder(file_path):
        folder_name = f"{os.path.splitext(os.path.basename(file_path))[0]}.{os.path.splitext(os.path.basename(file_path))[1][1:]}_pieces"
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    @staticmethod
    def receive_and_save_file_pieces(file_path, folder_name):
        with open(file_path, 'rb') as file:
            piece_number = 1
            while True:
                data = file.read(Torrent.PEDAZO_TAM)
                if not data:
                    break
                piece_path = os.path.join(folder_name, f"piece_{piece_number}.dat")
                with open(piece_path, 'wb') as piece_file:
                    piece_file.write(data)
                piece_number += 1

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        try:
            m = hashlib.new(Torrent.HASH_ALGORITHM)

            file_path = "archivos/" + sys.argv[3]
            file_obj = open(file_path, "rb")
            if file_obj:
                file_name = os.path.basename(file_path).split(".")[0]

                file_size = os.path.getsize(file_path)
                pieces_qty = int(file_size / Torrent.PEDAZO_TAM) + 1
                last_piece = file_size % Torrent.PEDAZO_TAM if pieces_qty > 1 else file_size


                pieces = Torrent.split_file(file_path)

                checksum = [Torrent.hash(m, piece) for piece in pieces]

                ip = sys.argv[1]
                puerto_tracker = int(sys.argv[2])

                with open(f"torrents/{file_name}.torrent", "w") as file:

                    torrent_obj = {
                        "pieces": pieces_qty,
                        "lastPiece": last_piece,
                        "filepath": file_path,
                        "tracker": ip,
                        "name": os.path.basename(file_path),
                        "checksum": checksum,
                        "puertoTracker": puerto_tracker,
                        "id": Torrent.hash(m, file_name.encode())
                    }

                    json.dump(torrent_obj, file, separators=(",", ":"))
                    print("Torrent creado!")


                folder_name = Torrent.create_pieces_folder(file_path)
                print(f"Carpeta de piezas creada: {folder_name}")

                Torrent.receive_and_save_file_pieces(file_path, folder_name)
        except FileNotFoundError as fe:
            print(fe)
        except IOError as ie:
            print(ie)
    else:

        print("Uso:")
        print("python Torrent.py <tracker_ip> <puerto_tracker> <file_name>")
