import sqlite3
import os
import pandas as pd
from datetime import datetime
from src.core.config import DB_PATH


def init_db(db_path: str = None):
    caminho = db_path or DB_PATH
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with sqlite3.connect(caminho) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_precos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo_busca TEXT NOT NULL,
                titulo TEXT NOT NULL,
                preco REAL NOT NULL,
                loja TEXT NOT NULL,
                condicao TEXT NOT NULL,
                link TEXT NOT NULL,
                data_consulta TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_termo ON historico_precos(termo_busca)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data ON historico_precos(data_consulta)")
        conn.commit()


def salvar_resultados(termo_busca: str, df: pd.DataFrame, db_path: str = None):
    """
    Salva os resultados no banco evitando duplicidades exatas no mesmo dia.
    """
    if df.empty:
        return
    caminho = db_path or DB_PATH
    agora = datetime.now()
    data_str = agora.strftime("%Y-%m-%d %H:%M:%S")
    data_dia = agora.strftime("%Y-%m-%d")
    termo_limpo = termo_busca.lower().strip()

    with sqlite3.connect(caminho) as conn:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                SELECT 1 FROM historico_precos
                WHERE termo_busca = ? AND titulo = ? AND loja = ? AND preco = ?
                  AND date(data_consulta) = ?
                LIMIT 1
            """, (termo_limpo, row["Título"], row["Loja"], row["Preço (R$)"], data_dia))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO historico_precos (termo_busca, titulo, preco, loja, condicao, link, data_consulta)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    termo_limpo,
                    row["Título"],
                    row["Preço (R$)"],
                    row["Loja"],
                    row.get("Condição", "Novo"),
                    row["Link"],
                    data_str
                ))
        conn.commit()


def carregar_historico_termo(termo_busca: str, db_path: str = None) -> pd.DataFrame:
    caminho = db_path or DB_PATH
    with sqlite3.connect(caminho) as conn:
        query = """
            SELECT titulo as "Título", preco as "Preço (R$)", loja as "Loja", condicao as "Condição", data_consulta as "Data"
            FROM historico_precos
            WHERE termo_busca = ?
            ORDER BY data_consulta DESC
            LIMIT 100
        """
        return pd.read_sql_query(query, conn, params=(termo_busca.lower().strip(),))


def carregar_evolucao_precos(termo_busca: str, db_path: str = None) -> pd.DataFrame:
    """
    Retorna a evolução histórica do menor preço e preço médio agrupado por data e loja.
    """
    caminho = db_path or DB_PATH
    with sqlite3.connect(caminho) as conn:
        query = """
            SELECT date(data_consulta) as "Data",
                   loja as "Loja",
                   MIN(preco) as "Menor Preço (R$)",
                   ROUND(AVG(preco), 2) as "Preço Médio (R$)",
                   COUNT(*) as "Ofertas"
            FROM historico_precos
            WHERE termo_busca = ?
            GROUP BY date(data_consulta), loja
            ORDER BY date(data_consulta) ASC
        """
        return pd.read_sql_query(query, conn, params=(termo_busca.lower().strip(),))


def listar_termos_buscados(db_path: str = None) -> list[str]:
    """Retorna os termos de busca recentes registrados no histórico."""
    caminho = db_path or DB_PATH
    if not os.path.exists(caminho):
        return []
    with sqlite3.connect(caminho) as conn:
        query = """
            SELECT DISTINCT termo_busca
            FROM historico_precos
            ORDER BY id DESC
            LIMIT 15
        """
        try:
            df = pd.read_sql_query(query, conn)
            return df["termo_busca"].str.title().tolist() if not df.empty else []
        except Exception:
            return []

