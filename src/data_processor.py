import pandas as pd
from config import CACHE_ENTRADA, PERFIL_ENTRADA, VOTACAO_ENTRADA
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
    df_votos = pd.read_csv(VOTACAO_ENTRADA, sep=";", encoding="latin1")
    df_votos = df_votos[df_votos["DS_CARGO"].isin(["Prefeito", "Vereador"])]

    df_votos["NM_MUNICIPIO"] = df_votos["NM_MUNICIPIO"].astype(str).str.strip().str.upper()
    df_votos["NM_LOCAL_VOTACAO"] = df_votos["NM_LOCAL_VOTACAO"].astype(str).str.strip().str.upper()
    df_principal["NM_MUNICIPIO"] = df_principal["NM_MUNICIPIO"].astype(str).str.strip().str.upper()
    df_principal["NM_LOCAL_VOTACAO"] = df_principal["NM_LOCAL_VOTACAO"].astype(str).str.strip().str.upper()

    votos_agrupados = df_votos.groupby(
        ["NM_MUNICIPIO", "NM_LOCAL_VOTACAO", "DS_CARGO", "NM_VOTAVEL"],
        as_index=False,
    )["QT_VOTOS"].sum()

    historico = []
    for (municipio, local), grupo in votos_agrupados.groupby(["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"]):
        historico.append({
            "NM_MUNICIPIO": municipio,
            "NM_LOCAL_VOTACAO": local,
            "HTML_CANDIDATOS": gerar_html_candidatos(grupo),
        })
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
            "HTML_CANDIDATOS"}
    cols = [c for c in df.columns if c not in base]
    preferidas = ["FEMININO", "MASCULINO", "NÃO INFORMADO"]
    ordenadas = [g for g in preferidas if g in cols]
    ordenadas += [g for g in cols if g not in ordenadas]
    return ordenadas
