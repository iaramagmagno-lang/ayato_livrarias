import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from src.core.utils import simplificar_termo_busca

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None


def coletar_amazon_http(termo: str) -> list[dict]:
    """Tentativa rápida de coleta na Amazon BR via requisição HTTP padrão."""
    livros = []
    termo_busca = simplificar_termo_busca(termo)
    termo_enc = urllib.parse.quote_plus(termo_busca)
    url = f"https://www.amazon.com.br/s?k={termo_enc}&i=stripbooks"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "Referer": "https://www.amazon.com.br/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200 and "Digite os caracteres que você vê" not in resp.text:
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select('div[data-component-type="s-search-result"], .s-result-item[data-asin]')
            for card in cards[:10]:
                titulo_el = card.select_one("h2 span, h2 a span")
                preco_inteiro = card.select_one(".a-price-whole")
                preco_fracao = card.select_one(".a-price-fraction")
                link_el = card.select_one("h2 a, a.a-link-normal.s-no-outline")

                if titulo_el and preco_inteiro and link_el:
                    titulo = titulo_el.get_text(strip=True)
                    p_int = re.sub(r"[^\d]", "", preco_inteiro.get_text(strip=True))
                    p_frac = re.sub(r"[^\d]", "", preco_fracao.get_text(strip=True)) if preco_fracao else "00"
                    try:
                        preco = float(f"{p_int}.{p_frac}")
                        href = link_el.get("href", "")
                        link_final = f"https://www.amazon.com.br{href.split('?')[0]}" if href.startswith("/") else href.split("?")[0]
                        livros.append({
                            "Título": titulo,
                            "Preço (R$)": preco,
                            "Loja": "Amazon BR",
                            "Condição": "Novo",
                            "Link": link_final
                        })
                    except ValueError:
                        continue
    except Exception as e:
        print(f"[Amazon HTTP] Erro: {e}")

    return livros


def coletar_amazon_stealth(termo: str) -> list[dict]:
    """
    Coleta na Amazon BR com tentativa rápida HTTP e fallback para Playwright.
    """
    resultados_http = coletar_amazon_http(termo)
    if resultados_http:
        return resultados_http

    if not sync_playwright:
        return []

    livros = []
    termo_busca = simplificar_termo_busca(termo)
    termo_enc = urllib.parse.quote_plus(termo_busca)
    url = f"https://www.amazon.com.br/s?k={termo_enc}&i=stripbooks"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                ),
                locale="pt-BR",
                viewport={"width": 1366, "height": 768}
            )
            page = context.new_page()

            if stealth_sync:
                stealth_sync(page)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=7000)

                html_text = page.content()
                if "Digite os caracteres que você vê" in html_text or "api-services-support@amazon.com" in html_text:
                    browser.close()
                    return []

                cards = page.query_selector_all('div[data-component-type="s-search-result"], .s-result-item[data-asin]')

                for card in cards[:10]:
                    titulo_el = card.query_selector("h2 span, h2 a span")
                    preco_inteiro = card.query_selector(".a-price-whole")
                    preco_fracao = card.query_selector(".a-price-fraction")
                    link_el = card.query_selector("h2 a, a.a-link-normal.s-no-outline")

                    if titulo_el and preco_inteiro and link_el:
                        titulo = titulo_el.inner_text().strip()
                        p_int = preco_inteiro.inner_text().replace(".", "").replace(",", "").strip()
                        p_frac = preco_fracao.inner_text().strip() if preco_fracao else "00"

                        try:
                            preco = float(f"{p_int}.{p_frac}")
                            href = link_el.get_attribute("href") or ""
                            link_final = (
                                f"https://www.amazon.com.br{href.split('?')[0]}"
                                if href.startswith("/") else href.split("?")[0]
                            )
                            livros.append({
                                "Título": titulo,
                                "Preço (R$)": preco,
                                "Loja": "Amazon BR",
                                "Condição": "Novo",
                                "Link": link_final
                            })
                        except ValueError:
                            continue
            except Exception as e:
                print(f"[Amazon] Timeout ou erro durante navegação: {e}")
            finally:
                browser.close()
    except Exception as e:
        print(f"[Amazon] Falha ao iniciar Playwright: {e}")

    return livros

