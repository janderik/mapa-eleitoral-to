import json
import pandas as pd
import folium
from folium import Html, Popup, Element
from folium.plugins import HeatMap

from config import COORDENADAS_CENTRO, ZOOM_INICIAL
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
        <div style="margin:6px 0;"><strong>{genero.title()}:</strong>
        <span style="color:{cor};font-weight:bold;">{int(qtd):,}</span></div>"""

    endereco_completo = f"{endereco}, {bairro}" if bairro else endereco
    if cep:
        endereco_completo += f" - CEP {cep}"

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;min-width:240px;max-height:75vh;overflow-y:auto;display:flex;flex-direction:column;padding:5px;">
        <h4 style="color:#2c3e50;margin:0 0 6px 0;border-bottom:2px solid #3498db;padding-bottom:8px;font-size:15px;flex-shrink:0;">
            {nome_local}
        </h4>
        <div style="font-size:12px;color:#7f8c8d;margin-bottom:10px;">
            <strong>Município:</strong> {municipio}<br>
            <strong>Endereço:</strong> {endereco_completo}
        </div>
        {itens}
        <hr style="border:none;border-top:1px solid #bdc3c7;margin:12px 0;">
        <div style="padding:10px;background:linear-gradient(135deg,#f5f7fa,#e4e8ec);border-radius:6px;text-align:center;">
            <span style="font-size:17px;color:#27ae60;font-weight:bold;">TOTAL: {int(total):,}</span>
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
    fg = folium.FeatureGroup(name="Locais de Votação")

    for _, row in df.iterrows():
        vals = {g: row[g] for g in generos if pd.notna(row[g]) and row[g] > 0}
        popup = criar_popup_premium(
            nome_local=row["NM_LOCAL_VOTACAO"],
            municipio=row["NM_MUNICIPIO"],
            endereco=row.get("DS_ENDERECO", ""),
            bairro=row.get("NM_BAIRRO", ""),
            cep=row.get("NR_CEP", ""),
            valores_genero=vals,
            total=row["TOTAL"],
            html_candidatos=row.get("HTML_CANDIDATOS", ""),
        )
        cor_icone = "red" if row.get("IS_VOLATIL") else "blue"
        folium.Marker(
            location=[row["NR_LATITUDE"], row["NR_LONGITUDE"]],
            popup=Popup(popup, max_width=380),
            icon=folium.Icon(color=cor_icone, icon="info-sign"),
            tooltip=f"{row['NM_LOCAL_VOTACAO']} ({row['NM_MUNICIPIO']})",
        ).add_to(fg)

    fg.add_to(mapa)

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

    cand_opts = ""
    if candidatos_list:
        cand_opts = "".join(f'<option value="{c}">' for c in candidatos_list)

    locais_candidatos = {}
    volatile_lookup = {}
    for _, row in df.iterrows():
        chave = f"{row['NM_MUNICIPIO']}|{row['NM_LOCAL_VOTACAO']}"
        locais_candidatos[chave] = json.loads(row.get("CANDIDATOS_LIST", "[]"))
        volatile_lookup[chave] = bool(row.get("IS_VOLATIL"))

    qtd_volateis = int(df['IS_VOLATIL'].sum())

    html_sidebar = f"""
    <style>
        #sidebar-toggle {{
            position:absolute; left:10px; bottom:10px; z-index:1000;
            background:rgba(0,0,0,0.6); color:#00ffcc;
            border:1px solid #00ffcc; backdrop-filter:blur(10px);
            padding:10px 14px; border-radius:5px; cursor:pointer;
            font-size:13px; font-weight:600; letter-spacing:0.5px;
            transition:all .3s ease;
        }}
        #sidebar-toggle:hover {{ background:rgba(0,255,204,0.15); }}
        #control-sidebar {{
            position:absolute; right:0; top:0; bottom:0; width:300px;
            background:rgba(18,18,24,0.97);
            border-left:1px solid #333; z-index:1000;
            padding:20px; overflow-y:auto;
            transform:translateX(100%);
            transition:transform 0.3s ease;
            font-family:'Segoe UI',Arial,sans-serif;
            box-shadow:-4px 0 24px rgba(0,0,0,0.5);
            display:flex; flex-direction:column; gap:14px;
        }}
        #control-sidebar.open {{ transform:translateX(0); }}
        #control-sidebar h2 {{
            color:#00ffcc; font-size:14px; font-weight:700; letter-spacing:1px;
            margin:0; padding-bottom:12px; border-bottom:2px solid #00ffcc;
            text-align:center;
        }}
        #control-sidebar label.section {{
            color:#888; font-size:10px; font-weight:600; letter-spacing:1.5px;
            margin-bottom:2px; text-transform:uppercase;
        }}
        #control-sidebar input[type="text"] {{
            width:100%; padding:10px 14px; font-size:13px;
            border:1px solid #333; border-radius:6px;
            background:rgba(0,0,0,0.4); color:#fff;
            outline:none; box-sizing:border-box;
            transition:border-color .2s;
        }}
        #control-sidebar input[type="text"]:focus {{
            border-color:#00ffcc;
        }}
        #control-sidebar .input-row {{
            display:flex; gap:4px;
        }}
        #control-sidebar .input-row button {{
            padding:10px 12px; font-size:12px;
            border:1px solid #666; border-radius:6px;
            background:rgba(0,0,0,0.4); color:#ccc;
            cursor:pointer; font-weight:bold; white-space:nowrap;
            transition:all .2s;
        }}
        #control-sidebar .input-row button:hover {{
            background:rgba(255,255,255,0.1);
        }}
        #control-sidebar .volatile-toggle {{
            display:flex; align-items:center; gap:10px;
            padding:12px; border:1px solid #ff3333; border-radius:6px;
            background:rgba(255,51,51,0.08);
            cursor:pointer; transition:all .3s;
            font-size:12px; font-weight:600; color:#ff4d4d;
        }}
        #control-sidebar .volatile-toggle.active {{
            background:rgba(255,51,51,0.25);
            border-color:#ff0000; color:#fff;
        }}
        #control-sidebar .volatile-toggle input {{
            display:none;
        }}
        #control-sidebar .volatile-toggle .check {{
            width:18px; height:18px; border:2px solid #ff3333;
            border-radius:4px; flex-shrink:0;
            display:flex; align-items:center; justify-content:center;
            transition:all .2s;
        }}
        #control-sidebar .volatile-toggle.active .check {{
            background:#ff3333;
        }}
        #control-sidebar .volatile-toggle .check::after {{
            content:'✓'; color:#fff; font-size:12px; font-weight:bold;
            display:none;
        }}
        #control-sidebar .volatile-toggle.active .check::after {{
            display:block;
        }}
    </style>
    <button id="sidebar-toggle" onclick="toggleSidebar()">⚙️ FILTROS</button>
    <div id="control-sidebar">
        <h2>INTELIGÊNCIA TÁTICA</h2>

        <label class="section">🔍 MUNICÍPIO</label>
        <input type="text" id="search-city" list="city-list" placeholder="Buscar município...">
        <datalist id="city-list">{opts}</datalist>

        <label class="section">🔎 CANDIDATO</label>
        <div class="input-row">
            <input type="text" id="search-candidate" list="candidate-list" placeholder="Filtrar por candidato..." style="flex:1;">
            <button id="clear-filter" title="Limpar filtro">✕</button>
        </div>
        <datalist id="candidate-list">{cand_opts}</datalist>

        <label class="section">⚡ ZONA DE RISCO</label>
        <div class="volatile-toggle" id="volatile-toggle-div" onclick="toggleVolatile()">
            <div class="check"></div>
            <span>ZONAS DE ALTA VOLATILIDADE ({qtd_volateis})</span>
        </div>
    </div>"""

    script_sidebar = f"""
var cityCoords = {json.dumps(coords_muni)};
var locationCandidates = {json.dumps(locais_candidatos)};
var volatileLookup = {json.dumps(volatile_lookup)};

function toggleSidebar() {{
    var sb = document.getElementById('control-sidebar');
    var btn = document.getElementById('sidebar-toggle');
    sb.classList.toggle('open');
    btn.textContent = sb.classList.contains('open') ? '✕ FECHAR' : '⚙️ FILTROS';
}}

document.addEventListener('click', function(e) {{
    var sb = document.getElementById('control-sidebar');
    var btn = document.getElementById('sidebar-toggle');
    if (sb.classList.contains('open') && !sb.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {{
        sb.classList.remove('open');
        btn.textContent = '⚙️ FILTROS';
    }}
}});

function getLocKeyFromLayer(layer) {{
    var tooltip = layer.getTooltip();
    if (!tooltip) return '';
    var content = tooltip.getContent();
    var idx = content.lastIndexOf(' (');
    if (idx === -1) return '';
    var locName = content.substring(0, idx);
    var muniName = content.substring(idx + 2, content.length - 1);
    return muniName + '|' + locName;
}}

document.getElementById('search-city').addEventListener('change', function(e) {{
    var cityName = e.target.value.toUpperCase().trim();
    if (cityCoords[cityName]) {{
        var leafletMap = window['{map_var}'];
        if (leafletMap) {{
            leafletMap.flyTo(cityCoords[cityName], 13, {{ animate: true, duration: 1.5 }});
        }}
    }}
}});

function highlightCandidate(candidateName) {{
    var leafletMap = window['{map_var}'];
    if (!leafletMap) return;
    var q = candidateName.toUpperCase().trim();
    var anyMatch = false;
    leafletMap.eachLayer(function(layer) {{
        if (!layer.getLatLng || !layer.setIcon) return;
        var key = getLocKeyFromLayer(layer);
        if (!key) return;
        var hasCandidate = locationCandidates[key] && locationCandidates[key].some(function(c) {{ return c.toUpperCase() === q; }});
        if (hasCandidate) {{
            anyMatch = true;
            layer.setOpacity(1.0);
            layer.setIcon(L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            }}));
        }} else {{
            layer.setOpacity(0.1);
        }}
    }});
    if (!anyMatch) {{
        resetFilter();
        document.getElementById('search-candidate').value = '';
        alert('Nenhum local encontrado com votações para este candidato.');
    }}
}}

function resetFilter() {{
    var leafletMap = window['{map_var}'];
    if (!leafletMap) return;
    leafletMap.eachLayer(function(layer) {{
        if (!layer.getLatLng || !layer.setIcon) return;
        layer.setOpacity(1.0);
        var key = getLocKeyFromLayer(layer);
        var isVolatil = volatileLookup[key] || false;
        layer.setIcon(L.icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-' + (isVolatil ? 'red' : 'blue') + '.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }}));
    }});
    document.getElementById('search-candidate').value = '';
}}

document.getElementById('search-candidate').addEventListener('change', function(e) {{
    if (e.target.value.trim()) {{
        highlightCandidate(e.target.value);
    }}
}});

document.getElementById('clear-filter').addEventListener('click', function() {{
    resetFilter();
    var cb = document.getElementById('volatile-toggle-div');
    if (cb.classList.contains('active')) {{
        cb.classList.remove('active');
    }}
}});

document.getElementById('search-candidate').addEventListener('keypress', function(e) {{
    if (e.key === 'Enter' && e.target.value.trim()) {{
        highlightCandidate(e.target.value);
    }}
}});

function toggleVolatile() {{
    var div = document.getElementById('volatile-toggle-div');
    var leafletMap = window['{map_var}'];
    if (!leafletMap) return;
    div.classList.toggle('active');
    var isActive = div.classList.contains('active');
    leafletMap.eachLayer(function(layer) {{
        if (!layer.getLatLng || !layer.setIcon) return;
        var key = getLocKeyFromLayer(layer);
        var isVolatil = volatileLookup[key] || false;
        if (isActive) {{
            if (isVolatil) {{
                layer.setOpacity(1.0);
                layer.setIcon(L.icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }}));
            }} else {{
                layer.setOpacity(0.1);
            }}
        }} else {{
            layer.setOpacity(1.0);
            layer.setIcon(L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-' + (isVolatil ? 'red' : 'blue') + '.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            }}));
        }}
    }});
}}
"""

    mapa.get_root().html.add_child(Element(html_sidebar))
    mapa.get_root().script.add_child(Element(script_sidebar))

    print(f"  -> {len(df)} marcadores adicionados")
    return mapa
