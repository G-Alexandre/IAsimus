import requests
import os
import time
import random
from requests.exceptions import ConnectionError, ReadTimeout

API_URL = "https://www.simus.com.br/wiki/api.php"
USERNAME = "cliente"
PASSWORD = "simus"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

session = requests.Session()

# Criar pasta local para imagens
if not os.path.exists("imagens"):
    os.makedirs("imagens")

# 1. Obter token de login
params1 = {
    "action": "query",
    "meta": "tokens",
    "type": "login",
    "format": "json"
}
r1 = session.get(API_URL, params=params1, headers=HEADERS)
login_token = r1.json()["query"]["tokens"]["logintoken"]

# 2. Fazer login
params2 = {
    "action": "login",
    "lgname": USERNAME,
    "lgpassword": PASSWORD,
    "lgtoken": login_token,
    "format": "json"
}
r2 = session.post(API_URL, data=params2, headers=HEADERS)
if r2.json().get("login", {}).get("result") != "Success":
    print("Erro ao logar:", r2.text)
    exit()

# 3. Listar imagens
imagens = []
aicontinue = ""
print("Listando imagens...")

while True:
    params = {
        "action": "query",
        "list": "allimages",
        "ailimit": "max",
        "format": "json"
    }
    if aicontinue:
        params["aicontinue"] = aicontinue

    r = session.get(API_URL, params=params, headers=HEADERS)
    if r.status_code != 200:
        print("Erro ao buscar lista de imagens:", r.status_code)
        break

    data = r.json()
    imagens += data["query"]["allimages"]

    if "continue" in data:
        aicontinue = data["continue"]["aicontinue"]
    else:
        break

print(f"Total de imagens encontradas: {len(imagens)}")
print("Iniciando downloads (somente novas imagens)...")

# 4. Baixar imagens com retry (somente se ainda não existem)
novas_baixadas = 0
for i, img in enumerate(imagens, start=1):
    nome = img["name"]
    url = img["url"]
    destino = os.path.join("imagens", nome)

    # 👉 Pular se a imagem já existe
    if os.path.exists(destino):
        continue

    for tentativa in range(5):
        try:
            r_img = session.get(url, headers=HEADERS, timeout=15)
            r_img.raise_for_status()
            with open(destino, "wb") as f:
                f.write(r_img.content)
            novas_baixadas += 1
            break  # sucesso
        except (ConnectionError, ReadTimeout) as e:
            print(f"[{i}/{len(imagens)}] Erro ao baixar '{nome}', tentativa {tentativa+1}/5: {e}")
            time.sleep(2 ** tentativa + random.uniform(0, 1))
        except Exception as e:
            print(f"[{i}/{len(imagens)}] Falha inesperada em '{nome}': {e}")
            break

    if novas_baixadas % 10 == 0 and novas_baixadas > 0:
        print(f"{novas_baixadas} novas imagens baixadas...")

print(f"Download finalizado! Total de novas imagens baixadas: {novas_baixadas}")
