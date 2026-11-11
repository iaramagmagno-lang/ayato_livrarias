import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from src.core.utils import simplificar_termo_busca


def coletar_travessa(termo: str, isbn: str = None) -> list[dict]:
    """
    Coleta ofertas na Livraria da Travessa (importante rede de livrarias físicas no Brasil).
    """
    livros = []
    termo_busca = isbn if (isbn and len(isbn) >= 10) else simplificar_termo_busca(termo)
    termo_enc = urllib.parse.quote_plus(termo_busca)
    url = f"https://www.travessa.com.br/busca?q={termo_enc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.travessa.com.br/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".vitrine-item, .produto-item, div[class*='produto'], div[class*='item']")
            for card in cards[:10]:
                titulo_el = card.find(["a", "h2", "h3"], class_=lambda x: x and any(k in str(x).lower() for k in ["titulo", "title", "nome"]))
                preco_el = card.find(["span", "div"], class_=lambda x: x and any(k in str(x).lower() for k in ["preco", "price", "valor"]))
                link_el = card.find("a", href=True)

                if titulo_el and preco_el and link_el:
                    titulo = titulo_el.get_text(strip=True)
                    match = re.search(r"(\d+(?:[.,]\d+)?)", preco_el.get_text(strip=True).replace(".", ""))
                    if match:
                        try:
                            preco = float(match.group(1).replace(",", "."))
                            href = link_el["href"]
                            link_final = f"https://www.travessa.com.br{href}" if href.startswith("/") else href
                            livros.append({
                                "Título": titulo,
                                "Preço (R$)": preco,
                                "Loja": "Livraria da Travessa",
                                "Condição": "Novo",
                                "Link": link_final.split("?")[0]
                            })
                        except ValueError:
                            continue
    except Exception as e:
        print(f"[Travessa] Erro: {e}")

    return livros

