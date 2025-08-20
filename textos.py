# textos.py
import requests
import time
import json
import random
import os
from datetime import datetime
from pathlib import Path
from requests.exceptions import ConnectionError, ReadTimeout

# --- Paths robustos (funciona como serviço) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "log"), exist_ok=True)

API_URL = "https://www.simus.com.br/wiki/api.php"
USERNAME = "cliente"
PASSWORD = "simus"
ARQUIVO_JSON = os.path.join(BASE_DIR, "wiki_simus.json")
LOG_DIR = os.path.join(BASE_DIR, "log")

session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def login() -> bool:
    try:
        r1 = session.get(API_URL, params={
            "action": "query", "meta": "tokens", "type": "login", "format": "json"
        }, headers=HEADERS, timeout=15)
        r1.raise_for_status()
        token = r1.json()["query"]["tokens"]["logintoken"]
        r2 = session.post(API_URL, data={
            "action": "login", "lgname": USERNAME, "lgpassword": PASSWORD,
            "lgtoken": token, "format": "json"
        }, headers=HEADERS, timeout=20)
        r2.raise_for_status()
        return r2.json().get("login", {}).get("result") == "Success"
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return False

def carregar_existentes():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            paginas = json.load(f)
            return paginas, {p.get("titulo", "") for p in paginas}
    return [], set()

def listar_todas_paginas():
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

        r = session.get(API_URL, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        for p in data["query"]["allpages"]:
            yield p["title"]

        if "continue" in data:
            apcontinue = data["continue"]["apcontinue"]
        else:
            break

def obter_conteudo_pagina(titulo: str) -> str:
    # Suporta API nova (slots) e antiga (*)
    for tentativa in range(5):
        try:
            params = {
                "action": "query",
                "format": "json",
                "prop": "revisions",
                "rvprop": "content",
                "titles": titulo
            }
            r = session.get(API_URL, params=params, headers=HEADERS, timeout=20)
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                rev = (page.get("revisions") or [{}])[0]
                if "slots" in rev and "main" in rev["slots"]:
                    return rev["slots"]["main"].get("*", "")
                return rev.get("*", "")
        except (ConnectionError, ReadTimeout):
            time.sleep(2 ** tentativa + random.uniform(0, 1))
        except Exception:
            break
    return ""

def salvar_log(novas_paginas_titulos):
    data_atual = datetime.now().strftime("%d_%m_%Y")
    nome_arquivo_status = os.path.join(LOG_DIR, f"status_atualizacao_{data_atual}.txt")
    with open(nome_arquivo_status, "w", encoding="utf-8") as f:
        if novas_paginas_titulos:
            f.write(f"✅ Foram extraídas {len(novas_paginas_titulos)} novas wikis.\n")
            f.write("Títulos:\n")
            for t in novas_paginas_titulos:
                f.write(f"- {t}\n")
        else:
            f.write("✅ Não foi encontrada nenhuma nova atualização.\n")

def main():
    if not login():
        print("❌ Erro ao fazer login.")
        salvar_log([])
        return

    paginas_existentes, titulos_existentes = carregar_existentes()

    titulos_novos = []
    for titulo in listar_todas_paginas():
        if titulo not in titulos_existentes:
            titulos_novos.append(titulo)

    novas_paginas = []
    for i, titulo in enumerate(titulos_novos, 1):
        conteudo = obter_conteudo_pagina(titulo)
        if conteudo is not None:
            novas_paginas.append({"titulo": titulo, "conteudo": conteudo})

    paginas_finais = paginas_existentes + novas_paginas
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(paginas_finais, f, indent=2, ensure_ascii=False)

    # Log com quantidade e títulos
    salvar_log([p["titulo"] for p in novas_paginas])

if __name__ == "__main__":
    main()
