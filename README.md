# BigFS - Sistema de Arquivos Distribuídos  
> Versão servidor : 2.7 | cliente : 2.5

## ✅ Funcionalidades

- 📂 Listagem de diretórios (`ls`)
- ❌ Remoção de arquivos (`rm`)
- 🔼 Upload de arquivos locais para o servidor (`cp ./arquivo.txt remoto/arquivo.txt`)
- 🔽 Download de arquivos do servidor para o cliente (`cp remoto/arquivo.txt ./arquivo.txt`)
- ❓ Ajuda interativa (`help`)

## 🧱 Arquitetura

O sistema segue uma arquitetura **cliente-servidor distribuída**, composta por:

- **Servidor (`bigfs_server_v2.py`)**
  Expõe a API de arquivos via Pyro4.
 
- **Cliente (`bigfs_client_v2.py`)** 
  Interface de linha de comando para enviar comandos ao servidor.

- **Shared (`protocol.py`)** 
  Implementa a lógica de manipulação de arquivos no lado do servidor, incluindo:
  - Escrita em fragmentos (`receive_file_chunk`)
  - Leitura em fragmentos (`send_file_chunk`)
  - Reset remoto de arquivos (`reset_file`)

A comunicação é feita via RPC usando **Pyro4** com suporte a **NameServer**.

## 🔌 Protocolo de Comunicação

1. O cliente localiza o servidor pelo **NameServer** (IP fixo necessário).
2. Um proxy Pyro é criado no cliente.
3. As chamadas remotas utilizam os métodos da classe `BigFSServer`, que encapsula um `BigFSProtocol`.

## ✅ Verificação de Integridade com SHA-256

Durante o upload (cliente → servidor):

    - Cada fragmento enviado tem seu hash SHA-256 calculado no cliente

    - Esse hash é enviado junto com o fragmento

    - O servidor recalcula o hash localmente e compara com o hash enviado

    - Se os hashes não baterem, o servidor rejeita o fragmento

Isso garante que cada fragmento individual chegou sem corrupção ou alteração.

## 🧬 Base64 na Transferência de Arquivos

    - Para garantir a integridade e evitar problemas com bytes especiais na comunicação via RPC, os fragmentos de arquivos são codificados em Base64 antes de serem enviados

    - No cliente:

        - Ao enviar (upload), o cliente lê o arquivo em bytes, codifica cada fragmento em Base64 e envia como string

        - Ao receber (download), o cliente decodifica os fragmentos Base64 recebidos de volta para bytes antes de gravar no disco

    - No servidor:

        - Recebe os fragmentos em Base64, decodifica para bytes para salvar no sistema de arquivos

        - Ao enviar um arquivo (download), codifica os fragmentos em Base64 para envio

## ⚠️ Limitações

- Sem autenticação ou controle de acesso
- Verificação de integridade somente para upload
- Sem replicação ou tolerância a falhas
- NameServer deve ser iniciado manualmente e requer IP fixo

## 🚀 Melhorias Futuras

- 🔐 Autenticação com HMAC
- 🌀 Replicação entre múltiplos servidores
- 📜 Log persistente e auditoria
- ✅ Verificação de integridade para Download
- 🧩 Modularização para múltiplos DataNodes

## 📁 Estrutura do Projeto

```
bigfs_rpc/
├── shared/
│ ├── __init__.py
│ └── protocol.py 
│
├── server/
│ └── bigfs_server_v2.py 
│
├── client/
│ └── bigfs_client_v2.py 
```

## 🧪 Como Executar

### 1. Inicie o NameServer

> Substitua `{IP}` pelo IP local da máquina na rede

```bash
pyro4-ns -n {IP}
```

### 2. Inicie o Servidor

> Execute no diretório raiz do projeto

```bash
PYTHONPATH=$(pwd) python3 server/bigfs_server_v2.py
```

### 3. Execute o cliente

```bash
python3 client/bigfs_client_v2.py
```
