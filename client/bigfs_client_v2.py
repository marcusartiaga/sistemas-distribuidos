#############################################
# bigfs_client.py                           #
#                                           #
# Cliente - v2.5                            #
#############################################

import Pyro4
import sys
import os
import base64

DEBUG = False

def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def print_help():
    print("""
Comandos disponíveis:

  ls [remoto/subdir]                 - Lista o conteúdo do diretório remoto
  cp remoto/arquivo.txt ./local.txt - Copia do servidor para o cliente
  cp ./local.txt remoto/arquivo.txt - Copia do cliente para o servidor
  rm remoto/arquivo.txt             - Remove arquivo no servidor
  exit                              - Sai do cliente
""")

def main():
    try:
        ns_ip = input("Digite o IP do Name Server (ex: 127.0.0.1): ").strip() or "127.0.0.1"
        debug_print(f"Buscando Name Server em {ns_ip}:9090")
        ns = Pyro4.locateNS(host=ns_ip, port=9090)
        uri = ns.lookup("bigfs.server")
        debug_print(f"URI do servidor encontrada: {uri}")
        server = Pyro4.Proxy(uri)
        debug_print("Proxy para servidor criado com sucesso")
    except Exception:
        print(f"[!] Servidor indisponível. Tente mais tarde.")
        return

    print("[*] Conectado ao servidor com sucesso!")
    print_help()

    while True:
        try:
            cmd = input("bigfs> ").strip()
            if not cmd:
                continue

            if cmd == "exit":
                print("[*] Encerrando conexão.")
                break

            elif cmd.startswith("ls"):
                parts = cmd.split()
                path = parts[1] if len(parts) > 1 else ""
                debug_print(f"Listando diretório remoto: /{path or 'remoto'}")
                print(f"=> /{path or 'remoto'}")
                result = server.ls(path)
                if isinstance(result, dict) and "error" in result:
                    print(f"[!] Erro: {result['error']}")
                else:
                    for item in result:
                        print(f"{item}/" if "." not in item else item)

            elif cmd.startswith("cp"):
                parts = cmd.split()
                if len(parts) != 3:
                    print("[?] Uso: cp <origem> <destino>")
                    continue

                src, dst = parts[1], parts[2]
                debug_print(f"Comando cp: {src} -> {dst}")

                # Download
                if src.startswith("remoto/") and not dst.startswith("remoto/"):
                    remote_path = src[len("remoto/"):]
                    try:
                        debug_print(f"Consultando tamanho do arquivo remoto '{remote_path}'")
                        total_size = server.get_file_size(remote_path)
                        if isinstance(total_size, dict) and 'error' in total_size:
                            raise Exception(total_size['error'])

                        with open(dst, "wb") as f:
                            chunk_size = 4096
                            offset = 0
                            total_received = 0

                            print("[*] Baixando arquivo do servidor...")
                            while True:
                                chunk = server.send_file_chunk(remote_path, offset, chunk_size)
                                if isinstance(chunk, dict) and 'error' in chunk:
                                    raise Exception(chunk['error'])

                                if isinstance(chunk, str):
                                    chunk = base64.b64decode(chunk)

                                if not isinstance(chunk, bytes):
                                    raise Exception(f"Chunk inválido: {type(chunk)}")

                                if len(chunk) == 0:
                                    break

                                f.write(chunk)
                                offset += len(chunk)
                                total_received += len(chunk)
                                progress = total_received / total_size * 100
                                if total_received % (chunk_size * 10) < chunk_size:
                                    print(f"\rProgresso: {progress:.2f}%", end="", flush=True)
                            print(f"\rProgresso: 100.00%")

                        print(f"\n[*] Download finalizado: remoto/{remote_path} => {dst}")

                    except Exception:
                        print(f"[!] Erro ao baixar o arquivo. Verifique no servidor.")

                # Upload
                elif dst.startswith("remoto/") and not src.startswith("remoto/"):
                    remote_path = dst[len("remoto/"):]

                    if not os.path.isfile(src):
                        print(f"[!] Arquivo local não encontrado: {src}")
                        continue

                    try:
                        file_size = os.path.getsize(src)
                        sent = 0
                        chunk_size = 4096
                        debug_print(f"Resetando arquivo remoto '{remote_path}' no servidor")
                        server.reset_file(remote_path)

                        print("[*] Enviando arquivo para o servidor...")
                        with open(src, "rb") as f:
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                chunk_base64 = base64.b64encode(chunk).decode('utf-8')

                                result = server.receive_file_chunk(remote_dst=remote_path, chunk_b64=chunk_base64)
                                if isinstance(result, dict) and 'error' in result:
                                    raise Exception(result['error'])

                                sent += len(chunk)
                                progress = sent / file_size * 100
                                if sent % (chunk_size * 10) < chunk_size:
                                    print(f"\rProgresso: {progress:.2f}%", end="", flush=True)

                            print(f"\rProgresso: 100.00%")

                        print(f"\n[*] Upload finalizado: {src} => remoto/{remote_path}")

                    except Exception:
                        print(f"[!] Erro ao enviar arquivo. Verifique no servidor.")

                else:
                    print("[!] Caminhos inválidos. Um deve ser remoto/, o outro local.")

            elif cmd.startswith("rm"):
                parts = cmd.split()
                if len(parts) != 2 or not parts[1].startswith("remoto/"):
                    print("[?] Uso: rm remoto/<arquivo>")
                    continue

                remote_path = parts[1][len("remoto/"):]
                debug_print(f"Solicitando remoção do arquivo remoto '{remote_path}'")
                result = server.delete(remote_path)
                if isinstance(result, dict) and "error" in result:
                    print(f"[!] Erro: {result['error']}")
                else:
                    print(f"[*] Arquivo remoto removido: {remote_path}")

            elif cmd == "help":
                print_help()

            else:
                print("[!] Comando inválido. Veja os comandos disponíveis com 'help'!")

        except Exception:
            print(f"[!] Erro inesperado. Verifique o servidor para mais detalhes.")

if __name__ == "__main__":
    main()

