import re
import requests
from bs4 import BeautifulSoup
from src.core.utils import simplificar_termo_busca, remover_acentos


def coletar_mercado_livre(termo: str, isbn: str = None) -> list[dict]:
    """
    Scraping na página de busca do Mercado Livre com suporte a ISBN prioritário.
    """
    livros = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    termo_limpo = simplificar_termo_busca(termo)
    slug = re.sub(r"[^\w\s-]", "", remover_acentos(termo_limpo)).strip().replace(" ", "-").lower()

    urls_para_tentar = []
    if isbn and len(isbn) >= 10:
        urls_para_tentar.append(f"https://lista.mercadolivre.com.br/{isbn}")
    urls_para_tentar.extend([
        f"https://lista.mercadolivre.com.br/livro-{slug}",
        f"https://lista.mercadolivre.com.br/{slug}"
    ])

    for url in urls_para_tentar:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".poly-card, .ui-search-result__wrapper, .ui-search-layout__item")
                if not cards:
                    continue

                for card in cards[:15]:
                    link_el = card.select_one("a.poly-component__title, a.ui-search-link, h2.ui-search-item__title a")
                    if not link_el:
                        continue
                    titulo = link_el.get_text(strip=True)
                    href = link_el.get("href", "")
                    if not titulo or not href:
                        continue

                    # Preço
                    fracao = card.select_one(".andes-money-amount__fraction")
                    if not fracao:
                        continue
                    centavos = card.select_one(".andes-money-amount__cents")
                    p_int = re.sub(r"[^\d]", "", fracao.get_text(strip=True))
                    p_cents = re.sub(r"[^\d]", "", centavos.get_text(strip=True)) if centavos else "00"

                    try:
                        preco = float(f"{p_int}.{p_cents}")
                    except ValueError:
                        continue

                    card_text = card.get_text().lower()
                    condicao = "Usado" if "usado" in card_text else "Novo"

                    livros.append({
                        "Título": titulo,
                        "Preço (R$)": preco,
                        "Loja": "Mercado Livre",
                        "Condição": condicao,
                        "Link": href.split("?")[0] if "?" in href else href
                    })

                if livros:
                    break
        except Exception as e:
            print(f"[Mercado Livre] Erro ao acessar {url}: {e}")

    return livros


# Retrocompatibilidade
coletar_mercado_livre_api = coletar_mercado_livre

