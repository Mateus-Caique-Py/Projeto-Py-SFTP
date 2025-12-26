# 📥 SFTP Downloader Automatizado

Script em **Python** para download automatizado de arquivos via **SFTP**, com lógica inteligente de data, barra de progresso em tempo real, organização por diretórios e renomeação padronizada dos arquivos após o download.

---

## 📌 Visão Geral

O **SFTP Downloader Automatizado** conecta-se a um servidor SFTP utilizando **chave SSH**, identifica arquivos com base em regras de data e padrões de nome, realiza o download com acompanhamento visual de progresso e organiza os arquivos localmente de forma padronizada.

O script foi projetado para **automação**, **robustez** e **uso corporativo**, podendo ser executado tanto em ambiente de desenvolvimento quanto empacotado como executável (`.exe`).

---

## ⚙️ Funcionalidades

- 🔐 Conexão segura via **SFTP com chave SSH**
- 📅 Lógica inteligente de data:
  - Segunda-feira → busca arquivos de sexta
  - Terça-feira → busca arquivos de segunda
  - Demais dias → busca arquivos do dia anterior
- 🔍 Filtro por:
  - Data no nome do arquivo
  - Padrões específicos de nomenclatura
  - Extensão `.csv`
- ⏪ Fallback automático para data anterior se nenhum arquivo for encontrado
- 📊 **Barra de progresso em tempo real**:
  - Percentual
  - Velocidade de download
  - Tempo estimado (ETA)
- 📂 Organização automática em diretórios distintos
- ✏️ Renomeação padronizada dos arquivos com sufixo numérico
- 📦 Compatível com execução como script ou executável (PyInstaller)

---

## 🛠️ Tecnologias Utilizadas

- Python 3.9+
- [Paramiko](https://www.paramiko.org/) (SFTP / SSH)
- Biblioteca padrão do Python:
  - `os`
  - `sys`
  - `time`
  - `datetime`

---

## 📁 Estrutura Esperada

```text
/
├── sftp_downloader.py
├── id_rsa               # Chave privada SSH
└── README.md
