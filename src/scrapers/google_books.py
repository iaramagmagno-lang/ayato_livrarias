import os
import requests

def _obter_api_key() -> str | None:
    """Tenta obter a chave de API do Google Books de secrets ou variáveis de ambiente."""
    key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GOOGLE_BOOKS_API_KEY")
        except Exception:
            pass
    return key


def buscar_metadados_google_books(termo: str) -> dict | None:
    """
    Obtém metadados do livro (capa, autor, sinopse, ISBN) pela API oficial do Google Books.
    """
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": termo,
        "maxResults": 3,
        "printType": "books",
        "langRestrict": "pt"
    }
    key = _obter_api_key()
    if key:
        params["key"] = key

    try:
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            dados = resp.json()
            itens = dados.get("items", [])
            if itens:
                volume = itens[0].get("volumeInfo", {})
                sale_info = itens[0].get("saleInfo", {})

                isbn = None
                for identifier in volume.get("industryIdentifiers", []):
                    if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
                        isbn = identifier.get("identifier")
                        break

                preco_google = None
                if sale_info.get("saleability") in ["FOR_SALE", "FOR_SALE_AND_RENTAL"]:
                    retail = sale_info.get("retailPrice") or sale_info.get("listPrice") or {}
                    if "amount" in retail:
                        preco_google = float(retail["amount"])

                return {
                    "titulo": volume.get("title", "Título desconhecido"),
                    "subtitulo": volume.get("subtitle", ""),
                    "autores": ", ".join(volume.get("authors", ["Autor desconhecido"])),
                    "publicado": volume.get("publishedDate", "N/A"),
                    "descricao": volume.get("description", "Sem descrição disponível."),
                    "capa": volume.get("imageLinks", {}).get("thumbnail", None),
                    "isbn": isbn,
                    "preco_google": preco_google,
                    "link_google": sale_info.get("buyLink", volume.get("infoLink", ""))
                }
        elif resp.status_code == 429:
            print("[Google Books Metadados] Cota diária anônima excedida (429).")
    except Exception as e:
        print(f"[Google Books Metadados] Erro: {e}")

    return None


def coletar_google_books(termo: str) -> list[dict]:
    """
    Coleta ofertas com preços reais da Google Play Livros Store.
    Rápido, oficial e 100% livre de bloqueios/captchas.
    """
    livros = []
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": termo,
        "maxResults": 10
    }
    key = _obter_api_key()
    if key:
        params["key"] = key

    try:
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            itens = resp.json().get("items", [])
            for item in itens:
                vol = item.get("volumeInfo", {})
                sale = item.get("saleInfo", {})
                titulo = vol.get("title")
                preco = None
                if sale.get("saleability") in ["FOR_SALE", "FOR_SALE_AND_RENTAL"]:
                    retail = sale.get("retailPrice") or sale.get("listPrice") or {}
                    if "amount" in retail:
                        preco = float(retail["amount"])

                link = sale.get("buyLink") or vol.get("infoLink")
                if titulo and preco and preco > 0 and link:
                    livros.append({
                        "Título": titulo,
                        "Preço (R$)": round(preco, 2),
                        "Loja": "Google Play Livros",
                        "Condição": "Digital",
                        "Link": link
                    })
        elif resp.status_code == 429:
            print("[Google Play Livros] Cota anônima excedida (429).")
    except Exception as e:
        print(f"[Google Play Livros] Erro: {e}")
    return livros
