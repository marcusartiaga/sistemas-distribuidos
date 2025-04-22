import socket
import os
import struct

HOST = 'localhost'
PORT = 5000

def recv_all(sock, size):
    data = b''
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            break
        data += part
    return data

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("[+] Conectado ao servidor.")

        while True:
            cmd = input("bigfs> ").strip()
            if not cmd:
                continue
            if cmd in ('exit', 'quit'):
                break

            parts = cmd.split()
            s.sendall(cmd.encode())

            if parts[0] == 'cp':
                response = s.recv(1024)
                if response != b"READY":
                    print(f"[ERRO] {response.decode()}")
                    continue

                for filename in parts[1:]:
                    try:
                        with open(filename, 'rb') as f:
                            content = f.read()

                        fname_bytes = os.path.basename(filename).encode().ljust(256, b'\x00')
                        size_bytes = struct.pack('!I', len(content))
                        s.sendall(fname_bytes + size_bytes)
                        s.sendall(content)

                        resp = s.recv(1024).decode()
                        print(resp)

                    except FileNotFoundError:
                        print(f"[ERRO] Arquivo '{filename}' não encontrado.")

            elif parts[0] == 'get':
                header = recv_all(s, 260)
                if not header or len(header) < 260:
                    print("[ERRO] Cabeçalho inválido.")
                    continue

                filename = header[:256].rstrip(b'\x00').decode()
                size = struct.unpack('!I', header[256:])[0]
                content = recv_all(s, size)

                if content is None:
                    print(f"[ERRO] Falha ao receber '{filename}'")
                    continue

                try:
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"[+] '{filename}' recebido com sucesso.")
                except Exception as e:
                    print(f"[ERRO] Erro ao salvar '{filename}': {e}")

                try:
                    leftover = s.recv(1024, socket.MSG_DONTWAIT)

                except BlockingIOError:
                    pass

            elif parts[0] == 'rm':
                data = s.recv(4096).decode()
                print(data)

            else:
                data = s.recv(4096).decode()
                print(f"\n{data}\n")

if __name__ == "__main__":
    main()

