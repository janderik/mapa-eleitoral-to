import pandas as pd


def _gerar_bloco_cargo(
    grupo: pd.DataFrame,
    cargo_nome: str,
    cargo_titulo: str,
    cor_barra: str,
    limite: int = None,
    abrir: bool = False,
) -> str:
    df_cargo = grupo[grupo["DS_CARGO"] == cargo_nome].sort_values("QT_VOTOS", ascending=False)
    if df_cargo.empty:
        return ""
    if limite is not None:
        df_cargo = df_cargo.head(limite)
    total_cargo = df_cargo["QT_VOTOS"].sum()
    linhas = ""
    for _, r in df_cargo.iterrows():
        pct = (r["QT_VOTOS"] / total_cargo) * 100 if total_cargo > 0 else 0
        linhas += (
            '<div style="margin:3px 0;">'
            '<div style="display:flex;justify-content:space-between;font-size:11px;">'
            f'<span style="color:#e0e0e0;font-weight:500;">{r["NM_VOTAVEL"]}</span>'
            f'<span style="color:{cor_barra};font-weight:600;">{int(r["QT_VOTOS"]):,}</span>'
            "</div>"
            '<div style="background:#333;border-radius:3px;height:5px;margin-top:2px;">'
            f'<div style="width:{pct:.1f}%;background:{cor_barra};height:5px;border-radius:3px;"></div>'
            "</div>"
            "</div>"
        )
    html_alerta = ""
    if cargo_nome == "PREFEITO" and len(df_cargo) >= 2:
        votos_1o = df_cargo.iloc[0]["QT_VOTOS"]
        votos_2o = df_cargo.iloc[1]["QT_VOTOS"]
        diferenca_pct = (votos_1o - votos_2o) / total_cargo if total_cargo > 0 else 1
        if diferenca_pct <= 0.05:
            html_alerta = (
                '<div style="background:rgba(255,0,0,0.1);border:1px solid #ff0000;color:#ff3333;padding:10px;'
                'border-radius:5px;margin-bottom:12px;text-align:center;font-size:11px;font-weight:bold;'
                'text-transform:uppercase;">'
                '⚠️ ZONA DE ALTA VOLATILIDADE (< 5% DE MARGEM)'
                '<br><span style="font-size:9px;color:#ff6666;font-weight:normal;text-transform:none;">'
                'Território vulnerável a virada de votos.</span></div>'
            )
    open_attr = " open" if abrir else ""
    return html_alerta + (
        f'<details{open_attr} style="margin-bottom:6px;background:#1a1a1a;border:1px solid #333;border-radius:5px;">'
        f'<summary style="background:#2a2a35;color:#ffffff;padding:10px;font-size:12px;font-weight:bold;cursor:pointer;outline:none;border-radius:4px;border-left:4px solid {cor_barra};transition:background 0.2s;position:sticky;top:0;z-index:10;">🗳️ {cargo_titulo}</summary>'
        f'<div style="max-height:40vh;overflow-y:auto;padding:6px;">{linhas}</div>'
        f"</details>"
    )


def _gerar_era(
    grupo: pd.DataFrame,
    cargos: list,
    cor_barra: str,
    rotulo: str,
    limite: int = None,
    abrir_primeiro: bool = False,
) -> str:
    blocos = ""
    for i, (cargo_nome, cargo_titulo) in enumerate(cargos):
        abrir = abrir_primeiro and i == 0
        blocos += _gerar_bloco_cargo(grupo, cargo_nome, cargo_titulo, cor_barra, limite, abrir)
    if not blocos:
        return ""
    return (
        f'<div style="background:transparent;color:#ffffff;font-size:12px;font-weight:bold;margin-bottom:8px;margin-top:15px;border-bottom:2px solid #444;padding-bottom:4px;letter-spacing:0.5px;text-transform:uppercase;position:sticky;top:0;z-index:10;">{rotulo}</div>'
        f"{blocos}"
    )


def gerar_html_candidatos(grupo_2024: pd.DataFrame, grupo_2022: pd.DataFrame) -> str:
    html_2024 = _gerar_era(
        grupo_2024,
        [("PREFEITO", "PREFEITO"), ("VEREADOR", "VEREADORES (LISTA COMPLETA)")],
        cor_barra="#00ffcc",
        rotulo="🟢 ELEIÇÕES MUNICIPAIS (2024)",
        abrir_primeiro=True,
    )
    html_2022 = _gerar_era(
        grupo_2022,
        [
            ("GOVERNADOR", "GOVERNADOR"),
            ("SENADOR", "SENADOR"),
            ("DEPUTADO FEDERAL", "DEPUTADO FEDERAL"),
            ("DEPUTADO ESTADUAL", "DEPUTADO ESTADUAL"),
        ],
        cor_barra="#2196f3",
        rotulo="🔵 ELEIÇÕES GERAIS (2022)",
        limite=3,
    )
    resultado = (html_2024 or "") + (html_2022 or "")
    if resultado:
        resultado += (
            '<div style="margin-top:10px;border-top:1px solid #333;padding-top:10px;">'
            '<button style="width:100%;background:#2980b9;color:#fff;border:1px solid #3498db;padding:8px;'
            'border-radius:4px;font-weight:bold;cursor:pointer;font-size:11px;"'
            ' onclick="alert(\'Módulo de Inteligência Econômica: Para mapear as lideranças deste setor, '
            'consulte a Matriz de CNPJs (Excel) integrada à plataforma.\')">'
            "📥 CONSULTAR MATRIZ DE LIDERANÇAS (OFFLINE)"
            "</button></div>"
        )
    return resultado


def gerar_painel_top10(df, map_var: str) -> str:
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

    painel_id = "top10-panel"
    body_id = "top10-body"
    toggle_id = "top10-toggle"

    return f"""
    <style>
        #{painel_id} {{
            position:absolute; top:12px; left:12px; z-index:9999;
            background:rgba(18,18,24,0.92);
            border:1px solid #2a2a3a; border-radius:10px;
            padding:14px 16px;
            font-family:'Segoe UI',Arial,sans-serif;
            color:#cfcfcf;
            max-height:85vh; overflow-y:auto;
            box-shadow:0 4px 24px rgba(0,0,0,0.6);
            min-width:320px;
            transition: all 0.3s ease;
        }}
        #{toggle_id} {{
            background:none; border:none; color:#00e676;
            font-size:18px; cursor:pointer; padding:0 4px;
            line-height:1; transition:transform 0.3s;
        }}
        #{toggle_id}:hover {{ transform:scale(1.2); }}
        @media (max-width: 768px) {{
            #{painel_id} {{
                min-width:auto; width:90vw; left:5vw; top:auto;
                bottom:10px; padding:10px 12px;
                font-size:11px;
                max-height:50vh;
            }}
            #{painel_id} table {{ font-size:10px !important; }}
            #{painel_id} th, #{painel_id} td {{ padding:2px 4px !important; }}
        }}
    </style>
    <div id="{painel_id}">
        <div style="display:flex;align-items:center;justify-content:space-between;
            font-size:14px; font-weight:700; color:#00e676; text-align:center;
            margin-bottom:8px; padding-bottom:8px;
            border-bottom:2px solid #00e676; letter-spacing:0.5px;">
            <span>TOP 10 COLÉGIOS ELEITORAIS - TO</span>
            <button id="{toggle_id}" onclick="toggleTop10()">−</button>
        </div>
        <div id="{body_id}">
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
        </div>
    </div>
    <script>
    function toggleTop10() {{
        var body = document.getElementById('{body_id}');
        var btn = document.getElementById('{toggle_id}');
        if (body.style.display === 'none') {{
            body.style.display = '';
            btn.textContent = '−';
        }} else {{
            body.style.display = 'none';
            btn.textContent = '+';
        }}
    }}
    if (window.innerWidth <= 768) {{
        var body = document.getElementById('{body_id}');
        var btn = document.getElementById('{toggle_id}');
        if (body) {{ body.style.display = 'none'; }}
        if (btn) {{ btn.textContent = '+'; }}
    }}
    </script>"""
