import requests
import time
import json
import random
import os
from datetime import datetime
from pathlib import Path
from requests.exceptions import ConnectionError, ReadTimeout

API_URL = "https://www.simus.com.br/wiki/api.php"
USERNAME = "cliente"
PASSWORD = "simus"
ARQUIVO_JSON = "wiki_simus.json"

session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Login
def login():
    token = session.get(API_URL, params={"action": "query", "meta": "tokens", "type": "login", "format": "json"}, headers=HEADERS).json()["query"]["tokens"]["logintoken"]
    r = session.post(API_URL, data={"action": "login", "lgname": USERNAME, "lgpassword": PASSWORD, "lgtoken": token, "format": "json"}, headers=HEADERS)
    return r.json()["login"]["result"] == "Success"

if not login():
    print("❌ Erro ao fazer login.")
    exit()

# Carrega titulos já existentes
if os.path.exists(ARQUIVO_JSON):
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        paginas_existentes = json.load(f)
        titulos_existentes = {p["titulo"] for p in paginas_existentes}
else:
    paginas_existentes = []
    titulos_existentes = set()

# Lista todas as páginas da Wiki
titulos_novos = []
apcontinue = ""
while True:
    params = {
        "action": "query",
        "list": "allpages",
        "aplimit": "max",
        "format": "json"
    }
    if apcontinue:
        params["apcontinue"] = apcontinue

    r = session.get(API_URL, params=params, headers=HEADERS)
    if r.status_code != 200:
        print("❌ Erro ao listar páginas:", r.status_code)
        break

    data = r.json()
    for p in data["query"]["allpages"]:
        titulo = p["title"]
        if titulo not in titulos_existentes:
            titulos_novos.append(titulo)

    if "continue" in data:
        apcontinue = data["continue"]["apcontinue"]
    else:
        break

# Busca conteúdos das novas páginas
novas_paginas = []
for i, titulo in enumerate(titulos_novos, 1):
    for tentativa in range(5):
        try:
            params = {
                "action": "query",
                "format": "json",
                "prop": "revisions",
                "rvprop": "content",
                "titles": titulo
            }
            r = session.get(API_URL, params=params, headers=HEADERS, timeout=10)
            r.raise_for_status()
            pages = r.json()["query"]["pages"]
            for _, page in pages.items():
                conteudo = page.get("revisions", [{}])[0].get("*", "")
                novas_paginas.append({"titulo": titulo, "conteudo": conteudo})
            break
        except (ConnectionError, ReadTimeout) as e:
            time.sleep(2 ** tentativa + random.uniform(0, 1))
        except Exception as e:
            break

# Junta as novas páginas ao arquivo antigo
paginas_finais = paginas_existentes + novas_paginas
with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(paginas_finais, f, indent=2, ensure_ascii=False)

# Cria a pasta log e salva status com data
Path("log").mkdir(exist_ok=True)
data_atual = datetime.now().strftime("%d_%m_%Y")
nome_arquivo_status = f"log/status_atualizacao_{data_atual}.txt"

with open(nome_arquivo_status, "w", encoding="utf-8") as f:
    if novas_paginas:
        f.write(f"Foram extraídas {len(novas_paginas)} novas wikis.")
    else:
        f.write("Não foi encontrada nenhuma nova atualização.")
