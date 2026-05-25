import pandas as pd
import folium
from folium import Html, Popup
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
    <div style="font-family:'Segoe UI',Arial,sans-serif;min-width:240px;padding:5px;">
        <h4 style="color:#2c3e50;margin:0 0 6px 0;border-bottom:2px solid #3498db;padding-bottom:8px;font-size:15px;">
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


def criar_mapa(df: pd.DataFrame) -> folium.Map:
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
        folium.Marker(
            location=[row["NR_LATITUDE"], row["NR_LONGITUDE"]],
            popup=Popup(popup, max_width=380),
            icon=folium.Icon(color="blue", icon="map-marker", prefix="fa"),
            tooltip=f"{row['NM_LOCAL_VOTACAO']} ({row['NM_MUNICIPIO']})",
        ).add_to(mapa)

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
    mapa.get_root().html.add_child(folium.Element(html_painel))

    print(f"  -> {len(df)} marcadores adicionados")
    return mapa
