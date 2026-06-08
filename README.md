# 🗺️ Plataforma de Inteligência Eleitoral — Tocantins

![Status](https://img.shields.io/badge/Status-Stable%20(MVP)-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Folium](https://img.shields.io/badge/Folium-0.16%2B-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> Dashboard georreferenciado de alta performance para análise tática de cenários eleitorais. Cruza dados demográficos do perfil eleitoral com resultados históricos de votação nominal (Municipais 2024 + Gerais 2022), transformando dados brutos do TSE em inteligência de território.

---

## 🚀 Funcionalidades

### 🔐 Controle de Acesso
Overlay de login com ofuscação Base64. Ideal para apresentações ao vivo sem expor o painel.

### 🔥 Mapa de Calor (Heatmap)
Renderização instantânea de zonas de alta densidade eleitoral — onde o ROI de campanha é maior.

### 📊 Métricas por Viewport
Painel dinâmico no sidebar que se atualiza ao mover/zoom:
- Total de eleitores e locais visíveis na tela
- Média de eleitores por local
- Distribuição por gênero (Feminino / Masculino / Não Informado) com barras coloridas
- Proporção de zonas estáveis vs voláteis
- Maior e menor local em eleitores na área visível

### 🎯 Filtro por Candidato
Campo de busca textual que filtra locais onde o candidato tem votação. Oculta os demais marcadores e recalcula as métricas automaticamente.

### ⚡ Zonas Voláteis
Identifica locais onde a margem entre 1º e 2º lugar em Prefeito é inferior a 5% — território vulnerável a virada de votos. Toggle para exibir/ocultar.

### 📐 Raio de Influência
Selecione um marcador e um raio (500m / 1km / 2km / 5km). O sistema desenha um círculo, escurece os marcadores fora do raio e exibe:
- Quantidade de locais de votação dentro do raio
- Total de eleitores na área

### ⚔️ Comparativo A vs B
Selecione dois candidatos nos dropdowns. Cada local é colorido:
- 🟢 Verde = Candidato A vence
- 🔵 Azul = Candidato B vence
- ⚫ Cinza = Empate
Barra de força no sidebar com os resultados numéricos. Círculos mantêm popups e tooltips originais.

### 🔍 Busca por Município
Autocomplete com `flyTo` suave: digite o nome do município e o mapa voa até ele.

### 🏆 Top 10 Colégios Eleitorais
Painel no canto superior esquerdo com os 10 municípios de maior eleitorado. Clique em qualquer um para voar até ele. Recolhível em mobile.

### 📄 Exportação de Relatório
Gera uma nova janela com relatório formatado para impressão contendo:
- Resumo geral (locais, estáveis, voláteis, municípios, total de eleitores)
- Raio de influência (se ativo)
- Top 10 locais por eleitorado
Usa `window.print()` — salve como PDF ou imprima.

### 🎯 Modo Apresentação
Remove sidebar, Top 10, controles de zoom e layers — foco total no mapa. Acesse pelo botão no sidebar. Saia com **✕ SAIR** ou **ESC**.

### 🎨 White-Label
Todas as cores e o nome do candidato são configuráveis em `src/config.py`:
- `COR_PRIMARIA`, `COR_SECUNDARIA`, `NOME_CANDIDATO`
- As cores são injetadas como CSS variables (`--cor-primaria`, `--cor-secundaria`)
- O overlay de login usa `NOME_CANDIDATO` e `COR_PRIMARIA` dinamicamente

### 🕰️ Timeline Eleitoral
Popups com accordion exibindo histórico completo:
- **Eleições Municipais (2024):** Prefeito e lista de Vereadores
- **Eleições Gerais (2022):** Governador, Senador, Deputado Federal e Estadual
Cada candidato com barra de progresso proporcional aos votos.

### 📱 Responsivo
Layout adaptado para mobile:
- Sidebar ocupa 100vw
- Botão de filtro vira FAB circular 55px
- Top 10 oculto em telas pequenas
- Popups com 90vw
- Inputs com 16px (anti-zoom iOS)

---

## 🏗️ Arquitetura

```
/
├── data/                        # Dados brutos do TSE (ignorados no Git)
│   ├── cache_geografico_to.csv  # Coordenadas dos locais de votação
│   ├── perfil_eleitor_secao_*.csv  # Perfil eleitoral por gênero
│   ├── votacao_secao_2024_TO.csv   # Resultados Eleições 2024
│   └── votacao_secao_2022_TO.csv   # Resultados Eleições 2022
│
├── src/                         # Pipeline Python
│   ├── config.py                # Constantes, cores, caminhos
│   ├── data_processor.py        # ETL: merge, normalização, histórico
│   ├── html_components.py       # Construtores de UI (popups, top 10)
│   ├── map_builder.py           # Orquestração Folium + sidebar + dados JS
│   └── main.py                  # Entry point + overlay de login
│
├── docs/                        # Saída estática (GitHub Pages)
│   ├── index.html               # Mapa completo compilado
│   └── assets/
│       ├── css/
│       │   └── style.css        # Estilos customizados + responsivo
│       └── js/
│           └── app.js           # Lógica frontend (sidebar, filtros, raio, etc.)
│
└── README.md
```

### Fluxo de Dados

```
CSVs TSE → data_processor.py (merge, normalização)
                  ↓
         html_components.py (popups HTML)
                  ↓
          map_builder.py (mapa Folium)
                  ↓
            main.py (overlay login)
                  ↓
         docs/index.html (GitHub Pages)
```

---

## 🔧 Como Executar o Build

```bash
pip install pandas folium
python src/main.py
```

O mapa será gerado em `docs/index.html`.

---

## ⚙️ Configuração White-Label

Edite `src/config.py`:

```python
COR_PRIMARIA = "#00ffcc"       # Cor principal (títulos, bordas, acentos)
COR_SECUNDARIA = "#00e676"     # Cor secundária (destaques, Top 10)
NOME_CANDIDATO = "Painel de Inteligência"  # Nome exibido no login
```

---

## 🔐 Acesso

O overlay de login usa ofuscação Base64 no frontend. A senha padrão é definida em `src/main.py`:

```javascript
if (btoa(input) === 'QUNFU1NPMjAyNg==')  // "ACESSO2026"
```

---

## 🧠 Bugs Conhecidos

| Bug | Causa | Solução |
|-----|-------|---------|
| Popup content é DOM node | Folium usa `$(html)[0]` | Extrair via `.outerHTML` |
| Script Folium executa depois do app.js | Ordem de carregamento | Polling (`setInterval`) até achar `window['map_*'] instanceof L.Map` |
| Marcadores dentro de FeatureGroup | Folium aninha layers | Iterar com `layer.eachLayer()` em grupos |
| Tooltip wrapper em HTML | Folium renderiza `<div>TEXTO</div>` | `stripHtmlAndTrim()` para extrair texto puro |

---

## 🌐 Publicação

O projeto é publicado via **GitHub Pages** a partir da pasta `docs/`:

```
https://janderik.github.io/mapa-eleitoral-to/
```

Basta fazer push no branch `main` que o GitHub Pages atualiza automaticamente.

---

## 📌 Status do Projeto

✅ **MVP Estável** — Funcionalidades implementadas e em produção.

---

*Desenvolvido com foco em precisão de dados e inteligência estratégica.*
