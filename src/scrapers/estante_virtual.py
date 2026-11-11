import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from src.core.utils import simplificar_termo_busca


def coletar_estante_virtual(termo: str, isbn: str = None) -> list[dict]:
    """
    Coleta na Estante Virtual com suporte a múltiplos livros e links resilientes.
    Suporta tanto botões Vue quanto tags <a> tradicionais.
    """
    livros = []
    # Prioriza o termo do livro para não restringir a uma única edição/código de barras
    termo_busca = simplificar_termo_busca(termo)
    termo_enc = urllib.parse.quote_plus(termo_busca)
    url = f"https://www.estantevirtual.com.br/busca?q={termo_enc}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.estantevirtual.com.br/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".product-item, .product-list__item")

            for card in cards[:25]:
                titulo_el = card.select_one(".product-item__title, h2, h3")
                preco_el = card.select_one(".product-item__sale-price, [data-auto='price']") or card.find(
                    lambda e: e.name in ["span", "p", "div"] and "R$" in e.text
                )

                if titulo_el and preco_el:
                    titulo = titulo_el.get_text(strip=True)
                    match = re.search(r"(\d+(?:[.,]\d+)?)", preco_el.get_text(strip=True).replace(".", ""))
                    if match:
                        try:
                            preco = float(match.group(1).replace(",", "."))
                            
                            # Extração de link resiliente
                            link_el = card.select_one("a[href]")
                            href = link_el.get("href", "") if link_el else ""
                            if href and href != "#" and href != "/":
                                link_final = (
                                    f"https://www.estantevirtual.com.br{href}"
                                    if href.startswith("/") else href
                                )
                            elif card.get("data-code"):
                                slug = re.sub(r"[^\w\s-]", "", titulo.lower()).strip().replace(" ", "-")
                                link_final = f"https://www.estantevirtual.com.br/livro/{slug}-{card['data-code']}-BK"
                            else:
                                link_final = f"https://www.estantevirtual.com.br/busca?q={urllib.parse.quote_plus(titulo)}"

                            condicao = "Usado"
                            variacoes = card.select_one(".product-item__variations")
                            if variacoes:
                                txt_v = variacoes.get_text().lower()
                                if "novo" in txt_v and "usado" not in txt_v:
                                    condicao = "Novo"

                            livros.append({
                                "Título": titulo,
                                "Preço (R$)": round(preco, 2),
                                "Loja": "Estante Virtual",
                                "Condição": condicao,
                                "Link": link_final.split("?")[0]
                            })
                        except ValueError:
                            continue
    except Exception as e:
        print(f"[Estante Virtual] Erro: {e}")

    return livros
