import socket
import threading
import os
import struct

HOST = 'localhost'
PORT = 5000
STORAGE_DIR = 'server_storage'

os.makedirs(STORAGE_DIR, exist_ok=True)

def recv_all(conn, size):
    data = b''
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_client(conn, addr):
    print(f"[+] Nova conexão de {addr[0]}")

    with conn:
        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    break

                print(f"[{addr[0]}] Comando recebido: {data}")
                parts = data.split()
                if not parts:
                    continue

                cmd = parts[0]

                if cmd == 'ls':
                    path = parts[1] if len(parts) > 1 else ''
                    response = handle_ls(path)
                    conn.sendall(response.encode())

                elif cmd == 'cp':
                    conn.sendall(b"READY")

                    for _ in range(len(parts) - 1):
                        header = recv_all(conn, 260)
                        if not header:
                            continue

                        filename = header[:256].rstrip(b'\x00').decode()
                        filesize = struct.unpack('!I', header[256:])[0]

                        print(f"[{addr[0]}] Recebido cabeçalho para o arquivo '{filename}', Tamanho: {filesize} bytes")

                        content = recv_all(conn, filesize)
                        if content is None:
                            conn.sendall(f"[ERRO] Falha ao receber '{filename}'".encode())
                            continue

                        path = os.path.join(STORAGE_DIR, filename)
                        with open(path, 'wb') as f:
                            f.write(content)

                        conn.sendall(f"[*] '{filename}' recebido com sucesso.".encode())

                elif cmd == 'get':
                    for filename in parts[1:]:
                        file_path = os.path.join(STORAGE_DIR, filename)

                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            with open(file_path, 'rb') as f:
                                content = f.read()

                            name_bytes = filename.encode().ljust(256, b'\x00')
                            size_bytes = struct.pack('!I', len(content))

                            print(f"[{addr[0]}] Enviando cabeçalho: {filename} ({len(content)} bytes)")

                            conn.sendall(name_bytes + size_bytes)
                            conn.sendall(content)

                        else:
                            name_bytes = filename.encode().ljust(256, b'\x00')
                            size_bytes = struct.pack('!I', 0)
                            error_msg = f"[ERRO] Arquivo '{filename}' não encontrado.".encode()
                            conn.sendall(name_bytes + size_bytes)
                            conn.sendall(error_msg)

                elif cmd == 'rm':
                    response = ""

                    for filename in parts[1:]:
                        file_path = os.path.join(STORAGE_DIR, filename)

                        if os.path.exists(file_path) and os.path.isfile(file_path):

                            try:
                                os.remove(file_path)
                                response += f"[*] '{filename}' removido com sucesso.\n"

                            except Exception as e:
                                response += f"[ERRO] {filename}: {e}\n"
                        else:
                            response += f"[ERRO] '{filename}' não encontrado.\n"

                    conn.sendall(response.encode())

                elif cmd == "help":
                    help_text = (
                        "Comandos disponíveis:\n"
                        "  ls [diretório]              - Lista arquivos no diretório\n"
                        "  cp arquivo1 [arquivo2 ...]  - Envia arquivos do cliente para o servidor\n"
                        "  get arquivo1 [arquivo2 ...] - Baixa arquivos do servidor para o cliente\n"
                        "  rm arquivo1 [arquivo2 ...]  - Remove arquivos do servidor\n"
                        "  quit                        - Fecha a conexão\n"
                        "  help                        - Mostra esta mensagem de ajuda"
                    )
                    conn.sendall(help_text.encode())

                else:
                    conn.sendall(f"[ERRO] Comando desconhecido: {cmd}".encode())

            except Exception as e:
                print(f"[{addr}] Erro: {e}")

                try:
                    conn.sendall(f"[ERRO] {e}".encode())

                except:
                    pass

                break

def handle_ls(path):
    full_path = os.path.join(STORAGE_DIR, path)

    if not os.path.exists(full_path):
        return f"[ERRO] '{path}' não existe no servidor."

    if os.path.isfile(full_path):
        return path

    elif os.path.isdir(full_path):
        files = os.listdir(full_path)
        return '\n'.join(files) if files else "[vazio]"

    else:
        return f"[ERRO] Caminho inválido."

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor iniciado em {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()

