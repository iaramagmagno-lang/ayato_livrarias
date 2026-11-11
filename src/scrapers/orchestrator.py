from concurrent.futures import ThreadPoolExecutor, as_completed
from src.core.utils import eh_relevante
from src.scrapers.estante_virtual import coletar_estante_virtual
from src.scrapers.martins_fontes import coletar_martins_fontes
from src.scrapers.buscape import coletar_buscape


def coletar_todas_as_lojas_paralelo(termo: str, isbn: str = None) -> tuple[list[dict], dict[str, int]]:
    """
    Executa os scrapers das lojas ativas e funcionais em paralelo via Threads.
    Retorna a lista de livros filtrada por relevância e a contagem por loja.
    """
    termo_limpo = termo.strip()
    tarefas = {
        "Estante Virtual": lambda: coletar_estante_virtual(termo_limpo, isbn=isbn),
        "Martins Fontes": lambda: coletar_martins_fontes(termo_limpo, isbn=isbn),
        "Buscapé": lambda: coletar_buscape(termo_limpo, isbn=isbn)
    }

    todos_livros = []
    status_lojas = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futuros = {executor.submit(func): loja for loja, func in tarefas.items()}
        for futuro in as_completed(futuros):
            tarefa_nome = futuros[futuro]
            try:
                resultados = futuro.result(timeout=10)
                resultados_filtrados = [
                    item for item in resultados
                    if eh_relevante(item["Título"], termo_limpo) and item.get("Preço (R$)", 0) >= 4.0
                ]
                if resultados_filtrados:
                    for item in resultados_filtrados:
                        loja_real = item.get("Loja", tarefa_nome)
                        status_lojas[loja_real] = status_lojas.get(loja_real, 0) + 1
                else:
                    if tarefa_nome not in status_lojas:
                        status_lojas[tarefa_nome] = 0

                todos_livros.extend(resultados_filtrados)
            except Exception as e:
                print(f"[{tarefa_nome}] Falha na execução paralela: {e}")
                if tarefa_nome not in status_lojas:
                    status_lojas[tarefa_nome] = 0

    return todos_livros, status_lojas
