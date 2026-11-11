# Módulo de compatibilidade raiz -> aponta para a arquitetura modular src.database
from src.database.db_manager import (
    init_db,
    salvar_resultados,
    carregar_historico_termo,
    carregar_evolucao_precos,
    listar_termos_buscados,
    DB_PATH as DB_NAME
)
