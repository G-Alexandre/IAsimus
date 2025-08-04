import requests
import time
import json
import random
from requests.exceptions import ConnectionError, ReadTimeout

API_URL = "https://www.simus.com.br/wiki/api.php"
USERNAME = "cliente"
PASSWORD = "simus"

session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Passo 1: Obter token de login
params1 = {
    "action": "query",
    "meta": "tokens",
    "type": "login",
    "format": "json"
}
r1 = session.get(API_URL, params=params1, headers=HEADERS)

if r1.status_code != 200:
    print("Erro na requisição inicial:", r1.status_code)
    print(r1.text)
    exit()

try:
    login_token = r1.json()["query"]["tokens"]["logintoken"]
except Exception as e:
    print("Erro ao obter token de login:", e)
    print("Resposta bruta:", r1.text)
    exit()

# Passo 2: Login
params2 = {
    "action": "login",
    "lgname": USERNAME,
    "lgpassword": PASSWORD,
    "lgtoken": login_token,
    "format": "json"
}
r2 = session.post(API_URL, data=params2, headers=HEADERS)

if r2.status_code != 200 or r2.json().get("login", {}).get("result") != "Success":
    print("Erro ao fazer login:", r2.status_code)
    print(r2.text)
    exit()

# Passo 3: Obter token CSRF
params3 = {
    "action": "query",
    "meta": "tokens",
    "format": "json"
}
r3 = session.get(API_URL, params=params3, headers=HEADERS)

if r3.status_code != 200:
    print("Erro ao obter token CSRF:", r3.status_code)
    print(r3.text)
    exit()

csrf_token = r3.json()["query"]["tokens"]["csrftoken"]

# Passo 4: Listar todos os títulos
titulos = []
apcontinue = ""
print("Listando títulos...")
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
        print("Erro ao listar páginas:", r.status_code)
        break

    data = r.json()
    titulos += [p["title"] for p in data["query"]["allpages"]]
    if "continue" in data:
        apcontinue = data["continue"]["apcontinue"]
    else:
        break

print(f"Total de páginas encontradas: {len(titulos)}")

# Passo 5: Obter conteúdo das páginas com retry
paginas = []
print("Coletando conteúdos...")

for i, titulo in enumerate(titulos, start=1):
    for tentativa in range(5):  # até 5 tentativas
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
                paginas.append({"titulo": titulo, "conteudo": conteudo})
            break  # sucesso, sai do retry
        except (ConnectionError, ReadTimeout) as e:
            print(f"[{i}/{len(titulos)}] Erro de conexão em '{titulo}', tentativa {tentativa + 1}/5: {e}")
            time.sleep(2 ** tentativa + random.uniform(0, 1))  # backoff com jitter
        except Exception as e:
            print(f"[{i}/{len(titulos)}] Erro inesperado em '{titulo}': {e}")
            break

    if i % 10 == 0:
        print(f"{i}/{len(titulos)} páginas processadas...")

# Passo 6: Salvar os dados
with open("wiki_simus.json", "w", encoding="utf-8") as f:
    json.dump(paginas, f, indent=2, ensure_ascii=False)

print("Extração finalizada! Dados salvos em 'wiki_simus.json'")
