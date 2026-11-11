import urllib.parse
import requests
from src.core.utils import simplificar_termo_busca


def coletar_martins_fontes(termo: str, isbn: str = None) -> list[dict]:
    """
    Coleta ofertas na Livraria Martins Fontes Paulista via API oficial VTEX.
    Rápida, oficial, estável e 100% livre de bloqueios em qualquer servidor na nuvem.
    """
    livros = []
    termo_busca = simplificar_termo_busca(termo)
    # VTEX requer espaço codificado como %20 (urllib.parse.quote) para não disparar WAF
    termo_enc = urllib.parse.quote(termo_busca)
    url = f"https://www.martinsfontespaulista.com.br/api/catalog_system/pub/products/search?ft={termo_enc}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code in [200, 206]:
            produtos = resp.json()
            for prod in produtos[:15]:
                nome = prod.get("productName")
                link = prod.get("link")
                items = prod.get("items", [])
                preco = None
                if items:
                    sellers = items[0].get("sellers", [])
                    if sellers:
                        comm = sellers[0].get("commertialOffer", {})
                        p = comm.get("Price")
                        if p and p > 0:
                            preco = float(p)

                if nome and preco and link:
                    livros.append({
                        "Título": nome.strip(),
                        "Preço (R$)": round(preco, 2),
                        "Loja": "Martins Fontes",
                        "Condição": "Novo",
                        "Link": link.split("?")[0]
                    })
    except Exception as e:
        print(f"[Martins Fontes] Erro: {e}")

    return livros
