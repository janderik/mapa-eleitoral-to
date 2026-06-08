from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"

CACHE_ENTRADA = str(DATA_DIR / "cache_geografico_to.csv")
PERFIL_ENTRADA = str(DATA_DIR / "perfil_eleitor_secao_ATUAL_TO.csv")
VOTACAO_ENTRADA = str(DATA_DIR / "votacao_secao_2024_TO.csv")
VOTACAO_2022_ENTRADA = str(DATA_DIR / "votacao_secao_2022_TO.csv")
ARQUIVO_SAIDA_MAPA = str(DOCS_DIR / "index.html")

COORDENADAS_CENTRO = (-10.1753, -48.2982)
ZOOM_INICIAL = 7

COR_PRIMARIA = "#00ffcc"
COR_SECUNDARIA = "#00e676"
NOME_CANDIDATO = "Painel de Inteligência"
LOGO_URL = ""
