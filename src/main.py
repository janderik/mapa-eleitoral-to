from config import ARQUIVO_SAIDA_MAPA
from data_processor import ler_cache, processar_perfil, processar_votacao, mergedf
from map_builder import criar_mapa


def gerar_overlay_login() -> str:
    return """<div id="login-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: #1a1a1a; z-index: 999999; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: sans-serif; margin: 0;">
    <h2 style="color: #00ffcc; margin-bottom: 5px; text-transform: uppercase;">Painel de Intelig\u00eancia</h2>
    <p style="color: #aaa; margin-bottom: 25px; font-size: 14px;">Acesso Restrito - Autentica\u00e7\u00e3o Necess\u00e1ria</p>
    <input type="password" id="senha-input" placeholder="Digite a Chave" style="padding: 12px; font-size: 16px; border: 1px solid #333; border-radius: 5px; margin-bottom: 15px; width: 280px; text-align: center; background: #222; color: #fff; outline: none;">
    <button onclick="verificarSenha()" style="padding: 12px 20px; font-size: 16px; background-color: #00ffcc; color: #000; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 280px; transition: 0.3s;">AUTENTICAR</button>
    <p id="erro-msg" style="color: #ff4444; margin-top: 20px; display: none; font-weight: bold;">\u26a0 Chave incorreta.</p>
</div>
<script>
function verificarSenha() {
    var input = document.getElementById('senha-input').value;
    if (btoa(input) === 'QUNFU1NPMjAyNg==') {
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


def main():
    print("=" * 60)
    print("PIPELINE MASTER - MAPA ELEITORAL DO TOCANTINS")
    print("=" * 60)

    cache = ler_cache()
    perfil = processar_perfil()
    df = mergedf(cache, perfil)

    df_historico, candidatos_list = processar_votacao(df)

    df = df.merge(df_historico, on=["NM_MUNICIPIO", "NM_LOCAL_VOTACAO"], how="left")
    df["HTML_CANDIDATOS"] = df["HTML_CANDIDATOS"].fillna("")
    df["CANDIDATOS_LIST"] = df["CANDIDATOS_LIST"].fillna("[]")

    mapa = criar_mapa(df, candidatos_list)
    mapa.save(ARQUIVO_SAIDA_MAPA)

    with open(ARQUIVO_SAIDA_MAPA, "r", encoding="utf-8") as f:
        html = f.read()

    overlay = gerar_overlay_login()
    html = html.replace("<body>", "<body>\n" + overlay)

    with open(ARQUIVO_SAIDA_MAPA, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nMapa salvo: {ARQUIVO_SAIDA_MAPA}")
    print("=" * 60)
    print("PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    main()
