#############################################################
# protocol.py - v1.2                                               #
#                                                           #
# Implementa a lógica das operações do sistema de arquivos: #
#                                                           #
# ls - Lista diretórios no sistema de arquivos remoto       #
# cp - Copia arquivos locais para remoto e vice-versa       #
# rm - Remove um arquivo do sistema de arquivos remoto      #
#                                                           #
#############################################################

import os
import hashlib


class BigFSProtocol:
    def __init__(self, shared_dir):
        self.shared_dir = os.path.abspath(shared_dir)
        if not os.path.exists(self.shared_dir):
            os.makedirs(self.shared_dir)

    def _get_abs_path(self, relative_path):
        return os.path.abspath(os.path.join(self.shared_dir, relative_path.strip("/")))

    def ls(self, subdir=""):
        path = self._get_abs_path(subdir)
        if os.path.exists(path) and os.path.isdir(path):
            return os.listdir(path)
        raise FileNotFoundError(f"[!] Diretório não encontrado: {path}")

    def delete(self, file_path):
        path = self._get_abs_path(file_path)
        if os.path.exists(path):
            os.remove(path)
            return f"[*] {file_path} removido com sucesso."
        raise FileNotFoundError(f"[!] Arquivo não encontrado: {path}")


# Lógica para download e upload dividindo arquivos em blocos e validando o hash em SHA256

    def reset_file(self, remote_path):
        path = self._get_abs_path(remote_path)
        with open(path, 'wb'):
            pass
        return f"[*] {remote_path} reiniciado para upload."

    def receive_file_chunk(self, remote_path, chunk_bytes, chunk_hash):
        computed_hash = hashlib.sha256(chunk_bytes).hexdigest()
        if computed_hash != chunk_hash:
            raise ValueError(f"[!] Hash incorreto no chunk: esperado {chunk_hash}, recebido {computed_hash}")

        path = self._get_abs_path(remote_path)
        with open(path, 'ab') as f:
            f.write(chunk_bytes)
        return f"[*] Chunk gravado em {remote_path}"

    def get_file_chunks(self, remote_path, chunk_size=4096):
        path = self._get_abs_path(remote_path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"[!] Arquivo não encontrado: {path}")

        chunks = []
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_hash = hashlib.sha256(chunk).hexdigest()
                chunks.append((chunk, chunk_hash))
        return chunks
