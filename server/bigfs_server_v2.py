#############################################
# bigfs_server.py                           #
#                                           #
# Servidor - v2.7                           #
#############################################

import Pyro4
import Pyro4.naming
from Pyro4 import current_context
import traceback
import sys
import threading
import os
import hashlib
import base64
from shared.protocol import BigFSProtocol

DEBUG = False

def log(msg):
    if DEBUG:
        print(msg)

def handle_file_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            client_ip = None
            try:
                client_ip = current_context.client.sock.getpeername()[0]
            except:
                pass

            print(f"[!] Erro na função {func.__name__} para cliente {client_ip}: {e}")
            return {"error": str(e)}
    return wrapper

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class BigFSServer:
    def __init__(self, shared_dir):
        self.fs = BigFSProtocol(shared_dir)
        self.lock = threading.Lock()

    def ls(self, subdir=""):
        return self.fs.ls(subdir)

    @handle_file_errors
    def delete(self, file_path):
        with self.lock:
            client_ip = current_context.client.sock.getpeername()[0]
            log(f"[{client_ip}] removeu /{file_path}")
            return self.fs.delete(file_path)

    @handle_file_errors
    def reset_file(self, remote_dst):
        with self.lock:
            path = self.fs._get_abs_path(remote_dst)
            with open(path, 'wb') as f:
                pass
            return

    @handle_file_errors
    def receive_file_chunk(self, remote_dst, chunk_b64):
        with self.lock:
            client_ip = current_context.client.sock.getpeername()[0]
            log(f"[{client_ip}] Subindo arquivo '{remote_dst}'")

            if not isinstance(chunk_b64, str):
                return {"error": "Chunk recebido não é uma string (Base64)"}

            try:
                chunk_bytes = base64.b64decode(chunk_b64)
            except Exception as e:
                return {"error": f"Falha ao decodificar Base64: {str(e)}"}

            path = self.fs._get_abs_path(remote_dst)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, 'ab') as f:
                f.write(chunk_bytes)

            return "OK"

    @handle_file_errors
    def send_file_chunk(self, remote_src, offset, chunk_size):
        client_ip = current_context.client.sock.getpeername()[0]
        log(f"[{client_ip}] Baixando arquivo '{remote_src}' - offset {offset}")

        path = self.fs._get_abs_path(remote_src)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {remote_src}")

        with open(path, 'rb') as f:
            f.seek(offset)
            data = f.read(chunk_size)
            return base64.b64encode(data).decode('utf-8')

    @handle_file_errors
    def get_file_size(self, remote_src):
        path = self.fs._get_abs_path(remote_src)
        return os.path.getsize(path)

    @handle_file_errors
    def compute_checksum(self, remote_path, algo="sha256"):
        with self.lock:
            path = self.fs._get_abs_path(remote_path)
            h = hashlib.new(algo)
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()

def main():
    shared_dir = "/tmp/bigfs"
    ns = Pyro4.locateNS(host="172.16.0.10", port=9090)  # IP do NS
    daemon = Pyro4.Daemon(host="0.0.0.0")
    uri = daemon.register(BigFSServer(shared_dir))
    ns.register("bigfs.server", uri)
    print(f"[*] Servidor foi iniciado!")
    print(f"[*] Objeto foi registrado no NS: {uri}")

    try:
        daemon.requestLoop()
    finally:
        ns.remove("bigfs.server")
        print("[!] Servidor foi finalizado e objeto removido")

if __name__ == "__main__":
    main()

