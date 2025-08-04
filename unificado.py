import json
import re
from pathlib import Path

# Arquivo de entrada
ARQUIVO_ENTRADA = "wiki_simus.json"
PASTA_IMAGENS = "imagens"

# Verificar se o arquivo e pasta existem
if not Path(ARQUIVO_ENTRADA).exists():
    print(f"❌ Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
    exit()

if not Path(PASTA_IMAGENS).exists():
    print(f"❌ Pasta '{PASTA_IMAGENS}' não encontrada.")
    exit()

# Carregar conteúdo das páginas
with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as f:
    paginas = json.load(f)

# Obter nomes das imagens na pasta
nomes_imagens = {img.name for img in Path(PASTA_IMAGENS).glob("*")}

print(f"✅ Páginas carregadas: {len(paginas)}")
print(f"✅ Imagens encontradas: {len(nomes_imagens)}")

# Processar cada página
resultado = []
for i, pagina in enumerate(paginas, start=1):
    titulo = pagina.get("titulo", "sem título")
    conteudo = pagina.get("conteudo", "")
    imagens_usadas = []

    for nome_img in nomes_imagens:
        if re.search(re.escape(nome_img), conteudo, re.IGNORECASE):
            imagens_usadas.append(nome_img)

    resultado.append({
        "titulo": titulo,
        "conteudo": conteudo,
        "imagens": imagens_usadas
    })

    if i % 10 == 0 or i == len(paginas):
        print(f"🔄 Processadas {i}/{len(paginas)} páginas...")

# Salvar resultado
with open("conteudo_com_imagens.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("✅ Arquivo 'conteudo_com_imagens.json' salvo com sucesso.")
