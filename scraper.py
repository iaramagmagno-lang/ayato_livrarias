# Módulo de compatibilidade raiz -> aponta para a arquitetura modular src.scrapers
from src.core.utils import remover_acentos, simplificar_termo_busca, eh_relevante
from src.scrapers import (
    buscar_metadados_google_books,
    coletar_google_books,
    coletar_mercado_livre,
    coletar_mercado_livre_api,
    coletar_estante_virtual,
    coletar_martins_fontes,
    coletar_amazon_http,
    coletar_amazon_stealth,
    coletar_travessa,
    coletar_todas_as_lojas_paralelo
)
