import pandas as pd
from config import CACHE_ENTRADA, PERFIL_ENTRADA, VOTACAO_ENTRADA, VOTACAO_2022_ENTRADA
from html_components import gerar_html_candidatos


def ler_cache() -> pd.DataFrame:
    print(f"Lendo cache geográfico: {CACHE_ENTRADA}")
    df = pd.read_csv(CACHE_ENTRADA, sep=";")
    for col in ["NR_LATITUDE", "NR_LONGITUDE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"  -> {len(df)} locais carregados")
    return df


def processar_perfil() -> pd.DataFrame:
    print(f"Lendo perfil eleitoral: {PERFIL_ENTRADA}")
    df = pd.read_csv(
        PERFIL_ENTRADA,
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


def processar_votacao(df_principal: pd.DataFrame) -> pd.DataFrame:
    print("Lendo votação 2024...")
    df_2024 = pd.read_csv(VOTACAO_ENTRADA, sep=";", encoding="latin1")
    df_2024["DS_CARGO"] = df_2024["DS_CARGO"].astype(str).str.strip().str.upper()
    df_2024 = df_2024[df_2024["DS_CARGO"].isin(["PREFEITO", "VEREADOR"])]

    print("Lendo votação 2022...")
    df_2022 = pd.read_csv(VOTACAO_2022_ENTRADA, sep=";", encoding="latin1")
    df_2022["DS_CARGO"] = df_2022["DS_CARGO"].astype(str).str.strip().str.upper()
    df_2022 = df_2022[
        df_2022["DS_CARGO"].isin(
            ["GOVERNADOR", "SENADOR", "DEPUTADO FEDERAL", "DEPUTADO ESTADUAL"]
        )
    ]

    for chave in ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"]:
        df_2024[chave] = df_2024[chave].astype(str).str.strip().str.upper()
        df_2022[chave] = df_2022[chave].astype(str).str.strip().str.upper()
        df_principal[chave] = df_principal[chave].astype(str).str.strip().str.upper()

    grp_2024 = df_2024.groupby(
        ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_CARGO", "NM_VOTAVEL"],
        as_index=False,
    )["QT_VOTOS"].sum()

    grp_2022 = df_2022.groupby(
        ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_CARGO", "NM_VOTAVEL"],
        as_index=False,
    )["QT_VOTOS"].sum()

    historico = []
    locais = df_principal[["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"]].drop_duplicates()
    qtd_volateis = 0
    for _, row in locais.iterrows():
        m, l = row["NM_MUNICIPIO"], row["NM_LOCAL_VOTACAO"]
        g2024 = grp_2024[(grp_2024["NM_MUNICIPIO"] == m) & (grp_2024["NM_LOCAL_VOTACAO"] == l)]
        g2022 = grp_2022[(grp_2022["NM_MUNICIPIO"] == m) & (grp_2022["NM_LOCAL_VOTACAO"] == l)]

        is_volatil = False
        df_pref = g2024[g2024["DS_CARGO"] == "PREFEITO"].sort_values("QT_VOTOS", ascending=False)
        if len(df_pref) >= 2:
            total_pref = df_pref["QT_VOTOS"].sum()
            diferenca_pct = (df_pref.iloc[0]["QT_VOTOS"] - df_pref.iloc[1]["QT_VOTOS"]) / total_pref if total_pref > 0 else 1
            is_volatil = diferenca_pct <= 0.05
            if is_volatil:
                qtd_volateis += 1

        historico.append({
            "NM_MUNICIPIO": m,
            "NM_LOCAL_VOTACAO": l,
            "IS_VOLATIL": is_volatil,
            "HTML_CANDIDATOS": gerar_html_candidatos(g2024, g2022),
        })

    print(f"  -> {len(historico)} locais com histórico de votação")
    print(f"  DEBUG: Total de locais analisados: {len(locais)}")
    print(f"  DEBUG: Locais identificados como VOLÁTEIS: {qtd_volateis}")
    return pd.DataFrame(historico)


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


def colunas_genero(df: pd.DataFrame) -> list:
    from typing import List
    base = {"NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_ENDERECO", "NM_BAIRRO",
            "NR_CEP", "NR_LATITUDE", "NR_LONGITUDE", "TOTAL",
            "HTML_CANDIDATOS", "IS_VOLATIL"}
    cols = [c for c in df.columns if c not in base]
    preferidas = ["FEMININO", "MASCULINO", "NÃO INFORMADO"]
    ordenadas = [g for g in preferidas if g in cols]
    ordenadas += [g for g in cols if g not in ordenadas]
    return ordenadas
