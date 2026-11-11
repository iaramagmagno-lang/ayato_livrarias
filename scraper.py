# Módulo de compatibilidade raiz -> aponta para a arquitetura modular src.scrapers
from src.core.utils import remover_acentos, simplificar_termo_busca, eh_relevante
from src.scrapers import (
    buscar_metadados_google_books,
    coletar_estante_virtual,
    coletar_martins_fontes,
    coletar_buscape,
    coletar_todas_as_lojas_paralelo
)
