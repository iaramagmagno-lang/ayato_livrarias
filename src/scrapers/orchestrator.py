from concurrent.futures import ThreadPoolExecutor, as_completed
from src.core.utils import eh_relevante
from src.scrapers.google_books import coletar_google_books, buscar_metadados_google_books
from src.scrapers.mercadolivre import coletar_mercado_livre
from src.scrapers.estante_virtual import coletar_estante_virtual
from src.scrapers.martins_fontes import coletar_martins_fontes
from src.scrapers.amazon import coletar_amazon_stealth
from src.scrapers.travessa import coletar_travessa


def coletar_todas_as_lojas_paralelo(termo: str, isbn: str = None) -> tuple[list[dict], dict[str, int]]:
    """
    Executa os scrapers de todas as lojas em paralelo via Threads.
    Reduz o tempo total de resposta de ~18 segundos para ~3-4 segundos.
    Retorna a lista de livros filtrada por relevância e o status de contagem por loja.
    """
    termo_limpo = termo.strip()
    tarefas = {
        "Estante Virtual": lambda: coletar_estante_virtual(termo_limpo, isbn=isbn),
        "Martins Fontes": lambda: coletar_martins_fontes(termo_limpo, isbn=isbn),
        "Google Play Livros": lambda: coletar_google_books(termo_limpo),
        "Mercado Livre": lambda: coletar_mercado_livre(termo_limpo, isbn=isbn),
        "Amazon BR": lambda: coletar_amazon_stealth(termo_limpo),
        "Livraria da Travessa": lambda: coletar_travessa(termo_limpo, isbn=isbn)
    }

    todos_livros = []
    status_lojas = {}

    with ThreadPoolExecutor(max_workers=6) as executor:
        futuros = {executor.submit(func): loja for loja, func in tarefas.items()}
        for futuro in as_completed(futuros):
            loja = futuros[futuro]
            try:
                resultados = futuro.result(timeout=14)
                resultados_filtrados = [
                    item for item in resultados
                    if eh_relevante(item["Título"], termo_limpo) and item.get("Preço (R$)", 0) >= 4.0
                ]
                status_lojas[loja] = len(resultados_filtrados)
                todos_livros.extend(resultados_filtrados)
            except Exception as e:
                print(f"[{loja}] Falha na execução paralela: {e}")
                status_lojas[loja] = 0

    return todos_livros, status_lojas
