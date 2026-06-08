import json
import pandas as pd
import folium
from folium import Html, Popup, Element
from folium.plugins import HeatMap

from config import COORDENADAS_CENTRO, ZOOM_INICIAL, COR_PRIMARIA, COR_SECUNDARIA, NOME_CANDIDATO
from html_components import gerar_painel_top10
from data_processor import colunas_genero


def criar_popup_premium(
    nome_local: str,
    municipio: str,
    endereco: str,
    bairro: str,
    cep: str,
    valores_genero: dict,
    total: int,
    html_candidatos: str = "",
) -> Html:
    mapeamento_cores = {"FEMININO": "#e91e63", "MASCULINO": "#2196f3", "NÃO INFORMADO": "#9e9e9e"}
    itens = ""
    for genero, qtd in valores_genero.items():
        cor = mapeamento_cores.get(genero, "#607d8b")
        itens += f"""
        <div style="margin:4px 0;font-size:13px;font-weight:bold;color:#dddddd;">{genero.title()}: <span style="color:{cor};">{int(qtd):,}</span></div>"""

    endereco_completo = f"{endereco}, {bairro}" if bairro else endereco
    if cep:
        endereco_completo += f" - CEP {cep}"

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;min-width:240px;max-height:75vh;overflow-y:auto;display:flex;flex-direction:column;padding:5px;">
        <h3 style="color:#ffffff !important;font-size:16px;font-weight:800;text-transform:uppercase;margin-bottom:5px;margin-top:0;text-shadow:0 2px 4px rgba(0,0,0,0.5);">
            {nome_local}
        </h3>
        <div style="font-size:12px;color:#7f8c8d;margin-bottom:10px;">
            <strong>Município:</strong> {municipio}<br>
            <strong>Endereço:</strong> {endereco_completo}
        </div>
        {itens}
        <hr style="border:none;border-top:1px solid #bdc3c7;margin:12px 0;">
        <div style="padding:10px;background:#1e1e24;color:#00ffcc;border:1px solid #333;text-align:center;font-weight:bold;font-size:14px;border-radius:5px;margin-bottom:15px;box-shadow:inset 0 0 10px rgba(0,0,0,0.5);">
            <span style="font-size:17px;">TOTAL: {int(total):,}</span>
        </div>
        <hr style="margin:5px 0;border:1px solid #ccc;">
        {html_candidatos if html_candidatos else '<div style="color:#888;font-size:11px;text-align:center;padding:8px 0;">Sem histórico de votação nominal</div>'}
    </div>"""
    return Html(html, script=True)


def criar_mapa(df: pd.DataFrame, candidatos_list: list = None) -> folium.Map:
    print("Criando mapa interativo...")

    mapa = folium.Map(
        location=COORDENADAS_CENTRO,
        zoom_start=ZOOM_INICIAL,
        tiles="OpenStreetMap",
        name="OpenStreetMap (Padrão)",
    )

    mapa.get_root().header.add_child(folium.Element(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />'
    ))

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satélite",
    ).add_to(mapa)

    folium.TileLayer(
        tiles="CartoDB Dark_Matter",
        name="Modo Noturno",
    ).add_to(mapa)

    generos = colunas_genero(df)
    fg_standard = folium.FeatureGroup(name="Locais Estáveis")
    fg_volatil = folium.FeatureGroup(name="Zonas Voláteis")
    marker_data = {}

    for _, row in df.iterrows():
        vals = {g: row[g] for g in generos if pd.notna(row[g]) and row[g] > 0}
        popup_html = criar_popup_premium(
            nome_local=row["NM_LOCAL_VOTACAO"],
            municipio=row["NM_MUNICIPIO"],
            endereco=row.get("DS_ENDERECO", ""),
            bairro=row.get("NM_BAIRRO", ""),
            cep=row.get("NR_CEP", ""),
            valores_genero=vals,
            total=row["TOTAL"],
            html_candidatos=row.get("HTML_CANDIDATOS", ""),
        )
        lat, lng = row["NR_LATITUDE"], row["NR_LONGITUDE"]
        tooltip_text = f"{row['NM_LOCAL_VOTACAO']} ({row['NM_MUNICIPIO']})"
        marker_data[tooltip_text] = {
            "total": int(row["TOTAL"]),
            "lat": lat,
            "lng": lng,
            "is_volatil": bool(row.get("IS_VOLATIL")),
        }

        folium.Marker(
            location=[lat, lng],
            popup=Popup(popup_html, max_width=380),
            icon=folium.Icon(color="blue", icon="info-sign"),
            tooltip=tooltip_text,
        ).add_to(fg_standard)

        if row.get("IS_VOLATIL"):
            folium.Marker(
                location=[lat, lng],
                popup=Popup(popup_html, max_width=380),
                icon=folium.DivIcon(
                    html='<div class="marcador-batalha"></div>',
                    icon_size=(18, 18),
                    icon_anchor=(9, 9),
                ),
                tooltip=tooltip_text,
            ).add_to(fg_volatil)

    fg_standard.add_to(mapa)
    fg_volatil.add_to(mapa)
    fg_volatil_var = fg_volatil.get_name()
    fg_standard_var = fg_standard.get_name()

    data_heat = [
        [row["NR_LATITUDE"], row["NR_LONGITUDE"], row["TOTAL"]]
        for _, row in df.iterrows()
    ]
    HeatMap(
        data_heat,
        name="Mapa de Calor",
        min_opacity=0.4,
        max_zoom=14,
        radius=25,
        blur=15,
    ).add_to(mapa)

    folium.LayerControl().add_to(mapa)

    map_var = mapa.get_name()
    html_painel = gerar_painel_top10(df, map_var)
    mapa.get_root().html.add_child(Element(html_painel))

    coords_muni = {}
    for nome, grupo in df.groupby("NM_MUNICIPIO"):
        coords_muni[nome] = [grupo["NR_LATITUDE"].mean(), grupo["NR_LONGITUDE"].mean()]

    opts = "".join(f'<option value="{n}">' for n in sorted(coords_muni))

    qtd_volateis = int(df['IS_VOLATIL'].sum())

    mapa.get_root().html.add_child(Element('<link rel="stylesheet" href="assets/css/style.css">'))

    css_vars = f"""<style>
:root {{
    --cor-primaria: {COR_PRIMARIA};
    --cor-secundaria: {COR_SECUNDARIA};
    --nome-candidato: "{NOME_CANDIDATO}";
    --logo-url: "";
}}
</style>"""
    mapa.get_root().html.add_child(Element(css_vars))

    html_sidebar = f"""
    <button id="sidebar-toggle">⚙️ FILTROS</button>
    <div id="control-sidebar">
        <h2>INTELIGÊNCIA TÁTICA</h2>

        <label class="section">🔍 MUNICÍPIO</label>
        <input type="text" id="search-city" list="city-list" placeholder="Buscar município...">
        <datalist id="city-list">{opts}</datalist>

        <label class="section">🔎 CANDIDATO</label>
        <div class="input-row">
            <input type="text" id="input-candidato" placeholder="Filtrar por candidato..." style="flex:1;">
            <button id="btn-limpar-candidato" title="Limpar filtro">✕</button>
        </div>

        <label class="section">⚡ ZONA DE RISCO</label>
        <label class="volatile-toggle" id="volatile-toggle-label">
            <input type="checkbox" id="vulnerability-filter" checked>
            <span>ZONAS DE ALTA VOLATILIDADE ({qtd_volateis})</span>
        </label>

        <label class="section">📐 RAIO DE INFLUÊNCIA</label>
        <div class="input-row">
            <select id="raio-select" style="flex:1;padding:10px 14px;font-size:13px;border:1px solid #333;border-radius:6px;background:rgba(0,0,0,0.4);color:#fff;outline:none;box-sizing:border-box;">
                <option value="500">500 m</option>
                <option value="1000" selected>1 km</option>
                <option value="2000">2 km</option>
                <option value="5000">5 km</option>
            </select>
            <button id="btn-raio" title="Ativar/Desativar Raio">ATIVAR</button>
        </div>
        <div id="raio-info" style="display:none;padding:10px;background:#1e1e24;border:1px solid var(--cor-primaria,#00ffcc);border-radius:6px;color:#cfcfcf;font-size:12px;line-height:1.6;"></div>

        <label class="section">📄 RELATÓRIO</label>
        <button id="btn-exportar" style="width:100%;padding:10px 14px;font-size:12px;font-weight:700;letter-spacing:1px;border:2px solid var(--cor-primaria,#00ffcc);border-radius:6px;background:transparent;color:var(--cor-primaria,#00ffcc);cursor:pointer;">EXPORTAR RELATÓRIO</button>
    </div>"""

    script_data = f"""<script>
var cityCoords = {json.dumps(coords_muni)};
var markerData = {json.dumps(marker_data)};
var fgVolatilName = '{fg_volatil_var}';
var fgStandardName = '{fg_standard_var}';
</script>"""

    mapa.get_root().html.add_child(Element(html_sidebar))
    mapa.get_root().html.add_child(Element(script_data))
    mapa.get_root().html.add_child(Element('<script src="assets/js/app.js"></script>'))

    print(f"  -> {len(df)} marcadores adicionados")
    return mapa
