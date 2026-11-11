import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from src.core.utils import simplificar_termo_busca


def coletar_buscape(termo: str, isbn: str = None) -> list[dict]:
    """
    Coleta ofertas no Buscapé (maior agregador de preços do Brasil).
    Traz ofertas de grandes redes de varejo (Magazine Luiza, Amazon e Marketplaces)
    sem sofrer bloqueio de IP na nuvem.
    """
    livros = []
    termo_limpo = simplificar_termo_busca(termo)
    # Adiciona "livro" no termo de busca para filtrar produtos não relacionados
    termo_query = termo_limpo if "livro" in termo_limpo.lower() else f"livro {termo_limpo}"
    termo_enc = urllib.parse.quote(termo_query)
    url = f"https://www.buscape.com.br/search?q={termo_enc}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.google.com.br/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=9)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("article[data-testid='product-card'], div[data-testid='product-card']")

            for card in cards[:20]:
                t_el = card.select_one("h2[data-testid='product-card::name'], h2")
                p_el = card.select_one("div[data-testid='product-card::price'] strong, [data-testid='product-card::price']")
                m_el = card.select_one("div[data-area='merchant'] span, [class*='MerchantLink'] span")
                l_el = card.select_one("a[data-testid='product-card::card'], a[href]")

                if t_el and p_el and l_el:
                    titulo = t_el.get_text(strip=True)
                    p_text = p_el.get_text(strip=True)
                    match = re.search(r"(\d+(?:[.,]\d+)?)", p_text.replace(".", ""))
                    if match:
                        preco = float(match.group(1).replace(",", "."))
                        loja_orig = m_el.get_text(strip=True) if m_el else ""
                        loja = loja_orig if loja_orig else "Buscapé"
                        href = l_el.get("href", "")
                        link = f"https://www.buscape.com.br{href}" if href.startswith("/") else href

                        livros.append({
                            "Título": titulo,
                            "Preço (R$)": round(preco, 2),
                            "Loja": loja,
                            "Condição": "Novo",
                            "Link": link
                        })
    except Exception as e:
        print(f"[Buscapé] Erro: {e}")

    return livros
