import json
import re
from pathlib import Path
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_ENTRADA = os.path.join(BASE_DIR, "wiki_simus.json")
PASTA_IMAGENS = os.path.join(BASE_DIR, "imagens")
ARQUIVO_SAIDA = os.path.join(BASE_DIR, "conteudo_com_imagens.json")

if not Path(ARQUIVO_ENTRADA).exists():
    print(f"❌ Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
    raise SystemExit(1)

if not Path(PASTA_IMAGENS).exists():
    print(f"❌ Pasta '{PASTA_IMAGENS}' não encontrada.")
    raise SystemExit(1)

with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as f:
    paginas = json.load(f)

nomes_imagens = {img.name for img in Path(PASTA_IMAGENS).glob("*")}
print(f"✅ Páginas carregadas: {len(paginas)}")
print(f"✅ Imagens encontradas: {len(nomes_imagens)}")

resultado = []
for i, pagina in enumerate(paginas, start=1):
    titulo = pagina.get("titulo", "sem título")
    conteudo = pagina.get("conteudo", "")
    imagens_usadas = []

    for nome_img in nomes_imagens:
        if re.search(re.escape(nome_img), conteudo, re.IGNORECASE):
            imagens_usadas.append(nome_img)

    resultado.append({"titulo": titulo, "conteudo": conteudo, "imagens": imagens_usadas})

    if i % 10 == 0 or i == len(paginas):
        print(f"🔄 Processadas {i}/{len(paginas)} páginas...")

with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("✅ Arquivo 'conteudo_com_imagens.json' salvo com sucesso.")
