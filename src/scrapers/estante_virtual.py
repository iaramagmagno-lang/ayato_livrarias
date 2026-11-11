import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from src.core.utils import simplificar_termo_busca


def coletar_estante_virtual(termo: str, isbn: str = None) -> list[dict]:
    """
    Coleta na Estante Virtual com suporte a busca exata por ISBN e Next.js hydration.
    """
    livros = []
    termo_busca = isbn if (isbn and len(isbn) >= 10) else simplificar_termo_busca(termo)
    termo_enc = urllib.parse.quote_plus(termo_busca)
    url = f"https://www.estantevirtual.com.br/busca?q={termo_enc}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.estantevirtual.com.br/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. Tenta extrair dados do __NEXT_DATA__
            next_script = soup.find("script", id="__NEXT_DATA__")
            if next_script and next_script.string:
                try:
                    data = json.loads(next_script.string)
                    props = data.get("props", {}).get("pageProps", {})
                    products = (
                        props.get("searchResult", {}).get("products", [])
                        or props.get("products", [])
                        or props.get("items", [])
                    )
                    for item in products[:15]:
                        t = item.get("title") or item.get("name")
                        p = item.get("price") or item.get("bestPrice") or item.get("minimumPrice")
                        l = item.get("url") or item.get("link")
                        if t and p:
                            p_float = float(p)
                            l_full = f"https://www.estantevirtual.com.br{l}" if l and l.startswith("/") else (l or url)
                            livros.append({
                                "Título": t,
                                "Preço (R$)": p_float,
                                "Loja": "Estante Virtual",
                                "Condição": "Usado",
                                "Link": l_full.split("?")[0]
                            })
                except Exception:
                    pass

            # 2. Fallback de seletores HTML
            if not livros:
                cards = soup.select(
                    "article, [data-testid*='product'], div[class*='product'], div[class*='card'], .listing-item"
                )
                for card in cards[:12]:
                    titulo_el = card.find(
                        ["h2", "h3", "a"],
                        class_=lambda x: x and any(k in str(x).lower() for k in ["title", "livro", "name", "nome"])
                    )
                    preco_el = card.find(
                        ["span", "div", "p"],
                        class_=lambda x: x and any(k in str(x).lower() for k in ["price", "preco", "valor"])
                    )
                    link_el = card.find("a", href=True)

                    if titulo_el and preco_el and link_el:
                        titulo = titulo_el.get_text(strip=True)
                        preco_texto = preco_el.get_text(strip=True)
                        match = re.search(r"(\d+(?:[.,]\d+)?)", preco_texto.replace(".", ""))
                        if match:
                            try:
                                preco_float = float(match.group(1).replace(",", "."))
                                href = link_el["href"]
                                link_final = (
                                    f"https://www.estantevirtual.com.br{href}"
                                    if href.startswith("/") else href
                                )
                                livros.append({
                                    "Título": titulo,
                                    "Preço (R$)": preco_float,
                                    "Loja": "Estante Virtual",
                                    "Condição": "Usado",
                                    "Link": link_final.split("?")[0]
                                })
                            except ValueError:
                                continue
    except Exception as e:
        print(f"[Estante Virtual] Erro: {e}")

    return livros

