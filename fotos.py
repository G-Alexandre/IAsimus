import requests
import os
import time
import random
from requests.exceptions import ConnectionError, ReadTimeout

API_URL = "https://www.simus.com.br/wiki/api.php"
USERNAME = "cliente"
PASSWORD = "simus"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

session = requests.Session()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGENS_DIR = os.path.join(BASE_DIR, "imagens")
os.makedirs(IMAGENS_DIR, exist_ok=True)

# 1. Obter token de login
params1 = {"action": "query", "meta": "tokens", "type": "login", "format": "json"}
r1 = session.get(API_URL, params=params1, headers=HEADERS, timeout=20)
r1.raise_for_status()
login_token = r1.json()["query"]["tokens"]["logintoken"]

# 2. Fazer login
params2 = {
    "action": "login", "lgname": USERNAME, "lgpassword": PASSWORD,
    "lgtoken": login_token, "format": "json"
}
r2 = session.post(API_URL, data=params2, headers=HEADERS, timeout=20)
if r2.json().get("login", {}).get("result") != "Success":
    print("Erro ao logar:", r2.text)
    raise SystemExit(1)

# 3. Listar imagens
imagens = []
aicontinue = ""
print("Listando imagens...")

while True:
    params = {"action": "query", "list": "allimages", "ailimit": "max", "format": "json"}
    if aicontinue:
        params["aicontinue"] = aicontinue

    r = session.get(API_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    imagens += data["query"]["allimages"]

    if "continue" in data:
        aicontinue = data["continue"]["aicontinue"]
    else:
        break

print(f"Total de imagens encontradas: {len(imagens)}")
print("Iniciando downloads (somente novas imagens)...")

novas_baixadas = 0
for i, img in enumerate(imagens, start=1):
    nome = img["name"]
    url = img["url"]
    destino = os.path.join(IMAGENS_DIR, nome)

    if os.path.exists(destino):
        continue

    for tentativa in range(5):
        try:
            r_img = session.get(url, headers=HEADERS, timeout=30)
            r_img.raise_for_status()
            with open(destino, "wb") as f:
                f.write(r_img.content)
            novas_baixadas += 1
            break
        except (ConnectionError, ReadTimeout) as e:
            print(f"[{i}/{len(imagens)}] Erro em '{nome}', tentativa {tentativa+1}/5: {e}")
            time.sleep(2 ** tentativa + random.uniform(0, 1))
        except Exception as e:
            print(f"[{i}/{len(imagens)}] Falha inesperada em '{nome}': {e}")
            break

    if novas_baixadas and novas_baixadas % 10 == 0:
        print(f"{novas_baixadas} novas imagens baixadas...")

print(f"Download finalizado! Total de novas imagens baixadas: {novas_baixadas}")
