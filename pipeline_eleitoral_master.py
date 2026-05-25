import pandas as pd
import folium
from folium import Html, Popup
from folium.plugins import HeatMap
from typing import List
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class Config:
    CACHE_ENTRADA = "cache_geografico_to.csv"
    PERFIL_ENTRADA = "perfil_eleitor_secao_ATUAL_TO.csv"
    VOTACAO_ENTRADA = "votacao_secao_2024_TO.csv"
    ARQUIVO_SAIDA_MAPA = "index.html"
    COORDENADAS_CENTRO = (-10.1753, -48.2982)
    ZOOM_INICIAL = 7


def ler_cache() -> pd.DataFrame:
    print(f"Lendo cache geográfico: {Config.CACHE_ENTRADA}")
    df = pd.read_csv(Config.CACHE_ENTRADA, sep=";")
    for col in ["NR_LATITUDE", "NR_LONGITUDE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"  -> {len(df)} locais carregados")
    return df


def processar_perfil() -> pd.DataFrame:
    print(f"Lendo perfil eleitoral: {Config.PERFIL_ENTRADA}")
    df = pd.read_csv(
        Config.PERFIL_ENTRADA,
        sep=";",
        encoding="latin1",
        low_memory=False,
        usecols=["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_GENERO", "QT_ELEITORES"],
    )
    print(f"  -> {len(df)} linhas brutas")

    df_grp = df.groupby(
        ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_GENERO"],
        as_index=False,
    )["QT_ELEITORES"].sum()

    df_pivot = df_grp.pivot(
        index=["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"],
        columns="DS_GENERO",
        values="QT_ELEITORES",
    ).reset_index()
    df_pivot.columns.name = None
    df_pivot = df_pivot.fillna(0)

    col_genero = [c for c in df_pivot.columns if c not in ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"]]
    df_pivot["TOTAL"] = df_pivot[col_genero].sum(axis=1).astype(int)
    for c in col_genero:
        df_pivot[c] = df_pivot[c].astype(int)

    print(f"  -> {len(df_pivot)} locais após agrupamento")
    return df_pivot


def processar_votacao() -> pd.DataFrame:
    print(f"Lendo votação 2024: {Config.VOTACAO_ENTRADA}")
    df = pd.read_csv(Config.VOTACAO_ENTRADA, sep=";", encoding="latin1")
    print(f"  -> {len(df)} linhas brutas")

    df = df[df["DS_CARGO"] == "Prefeito"]
    print(f"  -> {len(df)} linhas após filtro Prefeito")

    votos_agrupados = df.groupby(
        ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "NM_VOTAVEL"],
        as_index=False,
    )["QT_VOTOS"].sum()

    idx = votos_agrupados.groupby(
        ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"],
    )["QT_VOTOS"].idxmax()

    df_vencedores = votos_agrupados.loc[idx, ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "NM_VOTAVEL", "QT_VOTOS"]].reset_index(drop=True)
    df_vencedores = df_vencedores.rename(columns={"NM_VOTAVEL": "NM_VOTAVEL_VENC"})
    print(f"  -> {len(df_vencedores)} locais com vencedor identificado")
    return df_vencedores


def mergedf(cache: pd.DataFrame, perfil: pd.DataFrame) -> pd.DataFrame:
    print("Fazendo merge dos dados...")
    df = perfil.merge(
        cache,
        on=["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"],
        how="inner",
    )
    df = df.dropna(subset=["NR_LATITUDE", "NR_LONGITUDE"])
    print(f"  -> {len(df)} locais com coordenadas válidas")
    return df


def colunas_genero(df: pd.DataFrame) -> List[str]:
    base = {"NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_ENDERECO", "NM_BAIRRO",
            "NR_CEP", "NR_LATITUDE", "NR_LONGITUDE", "TOTAL",
            "NM_VOTAVEL_VENC", "QT_VOTOS"}
    cols = [c for c in df.columns if c not in base]
    preferidas = ["FEMININO", "MASCULINO", "NÃO INFORMADO"]
    ordenadas = [g for g in preferidas if g in cols]
    ordenadas += [g for g in cols if g not in ordenadas]
    return ordenadas


def criar_popup_premium(
    nome_local: str,
    municipio: str,
    endereco: str,
    bairro: str,
    cep: str,
    valores_genero: dict,
    total: int,
    nm_votavel_venc: str = "Sem registro",
    qt_votos_venc: int = 0,
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
        <div style="background-color:#1a1a1a;color:#00ffcc;padding:5px;border-radius:4px;margin-top:5px;">
            <b>🏆 Vencedor (2024):</b> {nm_votavel_venc} ({qt_votos_venc} votos)
        </div>
    </div>"""
    return Html(html, script=True)


def criar_mapa(df: pd.DataFrame) -> folium.Map:
    print("Criando mapa interativo...")

    mapa = folium.Map(
        location=Config.COORDENADAS_CENTRO,
        zoom_start=Config.ZOOM_INICIAL,
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
            nm_votavel_venc=row.get("NM_VOTAVEL_VENC", "Sem registro"),
            qt_votos_venc=int(row.get("QT_VOTOS", 0)),
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
    total_geral_to = int(df["TOTAL"].sum())

    top10_agg = (
        df.groupby("NM_MUNICIPIO")
        .agg(
            TOTAL=("TOTAL", "sum"),
            LAT_MEDIA=("NR_LATITUDE", "mean"),
            LNG_MEDIA=("NR_LONGITUDE", "mean"),
        )
        .sort_values("TOTAL", ascending=False)
        .head(10)
        .reset_index()
    )

    linhas_tabela = ""
    for i, (_, r) in enumerate(top10_agg.iterrows(), 1):
        pct = (r["TOTAL"] / total_geral_to) * 100
        linhas_tabela += f"""
        <tr>
            <td style="text-align:center;padding:4px 6px;color:#00e676;font-weight:bold;width:30px;">{i:02d}</td>
            <td style="padding:4px 8px;cursor:pointer;color:#cfcfcf;transition:color .2s;"
                onmouseover="this.style.color='#00e676'"
                onmouseout="this.style.color='#cfcfcf'"
                onclick="{map_var}.flyTo([{r['LAT_MEDIA']:.6f}, {r['LNG_MEDIA']:.6f}], 12);">
                {r['NM_MUNICIPIO']}
            </td>
            <td style="text-align:right;padding:4px 8px;font-family:'Consolas',monospace;white-space:nowrap;">{int(r['TOTAL']):,}</td>
            <td style="text-align:right;padding:4px 8px;font-family:'Consolas',monospace;color:#00e676;white-space:nowrap;">{pct:.1f}%</td>
        </tr>"""

    html_painel = f"""
    <div style="
        position:absolute; top:12px; left:12px; z-index:9999;
        background:rgba(18,18,24,0.92);
        border:1px solid #2a2a3a; border-radius:10px;
        padding:14px 16px;
        font-family:'Segoe UI',Arial,sans-serif;
        color:#cfcfcf;
        max-height:85vh; overflow-y:auto;
        box-shadow:0 4px 24px rgba(0,0,0,0.6);
        min-width:320px;
    ">
        <div style="
            font-size:14px; font-weight:700;
            color:#00e676; text-align:center;
            margin-bottom:8px; padding-bottom:8px;
            border-bottom:2px solid #00e676;
            letter-spacing:0.5px;
        ">TOP 10 COLÉGIOS ELEITORAIS - TO</div>
        <div style="text-align:center;font-size:11px;color:#888;margin-bottom:10px;">
            Total do estado: <span style="color:#fff;font-weight:600;">{total_geral_to:,}</span> eleitores
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <thead>
                <tr style="border-bottom:1px solid #333; color:#888;">
                    <th style="padding:3px 6px;">#</th>
                    <th style="text-align:left;padding:3px 8px;">Município</th>
                    <th style="text-align:right;padding:3px 8px;">Eleitores</th>
                    <th style="text-align:right;padding:3px 8px;">%</th>
                </tr>
            </thead>
            <tbody>{linhas_tabela}</tbody>
        </table>
    </div>"""

    mapa.get_root().html.add_child(folium.Element(html_painel))

    print(f"  -> {len(df)} marcadores adicionados")
    return mapa


def main():
    print("=" * 60)
    print("PIPELINE MASTER - MAPA ELEITORAL DO TOCANTINS")
    print("=" * 60)

    cache = ler_cache()
    perfil = processar_perfil()
    df = mergedf(cache, perfil)

    df_vencedores = processar_votacao()
    df = df.merge(df_vencedores, on=["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"], how="left")
    df["NM_VOTAVEL_VENC"] = df["NM_VOTAVEL_VENC"].fillna("Sem registro")
    df["QT_VOTOS"] = df["QT_VOTOS"].fillna(0).astype(int)

    mapa = criar_mapa(df)
    mapa.save(Config.ARQUIVO_SAIDA_MAPA)

    with open(Config.ARQUIVO_SAIDA_MAPA, "r", encoding="utf-8") as f:
        html = f.read()

    overlay = """<div id="login-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: #1a1a1a; z-index: 999999; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: sans-serif; margin: 0;">
    <h2 style="color: #00ffcc; margin-bottom: 5px; text-transform: uppercase;">Painel de Intelig\u00eancia</h2>
    <p style="color: #aaa; margin-bottom: 25px; font-size: 14px;">Acesso Restrito - Autentica\u00e7\u00e3o Necess\u00e1ria</p>
    <input type="password" id="senha-input" placeholder="Digite a Chave" style="padding: 12px; font-size: 16px; border: 1px solid #333; border-radius: 5px; margin-bottom: 15px; width: 280px; text-align: center; background: #222; color: #fff; outline: none;">
    <button onclick="verificarSenha()" style="padding: 12px 20px; font-size: 16px; background-color: #00ffcc; color: #000; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 280px; transition: 0.3s;">AUTENTICAR</button>
    <p id="erro-msg" style="color: #ff4444; margin-top: 20px; display: none; font-weight: bold;">\u26a0 Chave incorreta.</p>
</div>
<script>
function verificarSenha() {
    var input = document.getElementById('senha-input').value;
    if (input === 'ACESSO2026') {
        var overlay = document.getElementById('login-overlay');
        overlay.style.opacity = '0';
        setTimeout(function() { overlay.style.display = 'none'; }, 500);
    } else {
        document.getElementById('erro-msg').style.display = 'block';
        document.getElementById('senha-input').value = '';
        document.getElementById('senha-input').focus();
    }
}
document.getElementById('senha-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') { verificarSenha(); }
});
</script>"""

    html = html.replace("<body>", "<body>\n" + overlay)

    with open(Config.ARQUIVO_SAIDA_MAPA, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nMapa salvo: {Config.ARQUIVO_SAIDA_MAPA}")
    print("=" * 60)
    print("PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    main()
