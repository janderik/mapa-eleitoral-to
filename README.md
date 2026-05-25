# 🗺️ Plataforma de Inteligência Geopolítica - Tocantins

![Status](https://img.shields.io/badge/Status-Stable%20(MVP)-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Data_Science](https://img.shields.io/badge/Data%20Science-Pandas%20%7C%20Folium-orange)
![Security](https://img.shields.io/badge/Security-Obfuscated%20Auth-red)

## 📌 Visão Executiva
Plataforma analítica desenvolvida para mapeamento tático e inteligência eleitoral no estado do Tocantins. O sistema cruza macrodados demográficos com resultados históricos de votação nominal (Eleições Municipais de 2024 e Gerais de 2022), transformando dados brutos do TSE em um **Dashboard Georreferenciado** de alta performance.

## 🚀 Funcionalidades Principais (Features)

* **🔐 Controle de Acesso (Overlay Auth):** Interface estática protegida por camada visual de autenticação e ofuscação de credenciais, garantindo sigilo tático em apresentações.
* **🔥 Heatmap de Densidade Eleitoral:** Renderização instantânea de zonas de alta pressão de votos (onde o ROI de campanha é maior).
* **⏳ Máquina do Tempo Eleitoral (Split View):** Popups dinâmicos em HTML5 puro (Accordions) que exibem a retenção de território, divididos em:
  * *Eleições Municipais (2024):* Prefeito (Vencedor) e lista completa de Vereadores.
  * *Eleições Gerais (2022):* Top 3 candidatos para Presidente, Governador, Senador, Deputados Federal e Estadual.
* **🚁 Navegação Cinematográfica (Autocomplete):** Barra de pesquisa flutuante conectada à API nativa do Leaflet (`flyTo`), permitindo saltos de precisão entre os 139 municípios do estado em milissegundos.
* **📱 UI/UX Responsiva:** Painel retrátil de Top 10 Colégios Eleitorais otimizado para dispositivos móveis (Mobile-First).

## 🏗️ Arquitetura do Projeto (Padrão Sênior)

O repositório adota uma arquitetura modular baseada nos princípios SOLID, separando a camada de dados brutos da lógica de renderização:

```text
/
├── data/                  # Data Lake (Ignorado no Git por questões de limite e sigilo)
│   ├── cache_geografico_to.csv
│   ├── perfil_eleitor_secao_ATUAL_TO.csv
│   ├── votacao_secao_2024_TO.csv
│   └── votacao_secao_2022_TO.csv
├── src/                   # Core / Motor de Processamento
│   ├── config.py          # Constantes e roteamento de arquivos
│   ├── data_processor.py  # Pipeline de ETL (Pandas, Merge, Normalização de Chaves)
│   ├── html_components.py # Construtores de UI (Accordions, Tabelas, CSS in-line)
│   ├── map_builder.py     # Orquestração do Folium (Heatmap, Markers, Search Bar)
│   └── main.py            # Entry point e Injeção de Segurança Frontend
└── docs/                  # Build Directory (Consumido pelo GitHub Pages)
    └── index.html         # Output final do Dashboard Interativo
```

## 🛡️ Governança e Segurança
A arquitetura foi desenhada considerando mitigações de segurança para ambientes Serverless (GitHub Pages). O mapeamento das chaves do TSE passa por um processo rigoroso de sanitização de strings (strip, upper) para evitar perda de dados no Merge. Como se trata de um site estático, mecanismos de ofuscação são aplicados no frontend para dificultar o scraping da chave de acesso.

## 🛠️ Como Executar o Build
Para compilar uma nova versão do mapa após a atualização da pasta /data:

1. Instale as dependências: `pip install pandas folium`
2. Execute o orquestrador: `python src/main.py`
3. O novo mapa será gerado em `docs/index.html`.

---

*Desenvolvido com foco em precisão de dados e inteligência estratégica.*
