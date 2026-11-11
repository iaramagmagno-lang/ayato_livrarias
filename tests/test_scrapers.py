import sys
import os
import pytest
import pandas as pd
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.utils import (
    remover_acentos,
    simplificar_termo_busca,
    eh_relevante
)
from src.services.exporters import (
    gerar_csv_profissional,
    gerar_excel_profissional
)
from src.database.db_manager import (
    init_db,
    salvar_resultados,
    carregar_historico_termo,
    carregar_evolucao_precos
)


def test_remover_acentos():
    assert remover_acentos("O Pequeno Príncipe") == "O Pequeno Principe"
    assert remover_acentos("Atenção e Ação") == "Atencao e Acao"
    assert remover_acentos("Épico & História") == "Epico & Historia"


def test_simplificar_termo_busca():
    assert simplificar_termo_busca("Clean Code: A Handbook of Agile Software") == "Clean Code"
    assert simplificar_termo_busca("Duna - Edição Especial") == "Duna"
    assert simplificar_termo_busca("Sapiens") == "Sapiens"


def test_eh_relevante_livros():
    assert eh_relevante("Livro Clean Code - Robert C. Martin", "Clean Code") is True
    assert eh_relevante("Clean Code - Habilidades Práticas do Agile", "Clean Code") is True
    assert eh_relevante("O Pequeno Príncipe - Capa Dura", "O Pequeno Príncipe") is True


def test_eh_relevante_bloqueia_acessorios():
    assert eh_relevante("Camiseta Clean Code Programador", "Clean Code") is False
    assert eh_relevante("Caneca Dev Clean Code Cerâmica", "Clean Code") is False
    assert eh_relevante("Adesivo Notebook Clean Code", "Clean Code") is False
    assert eh_relevante("Poster Quadro Decorativo Clean Code", "Clean Code") is False


def test_gerar_csv_profissional():
    df = pd.DataFrame([{
        "Título": "Clean Code",
        "Loja": "Mercado Livre",
        "Condição": "Novo",
        "Preço (R$)": 49.90,
        "Link": "https://mercadolivre.com.br/item"
    }])

    csv_bytes = gerar_csv_profissional(df, "Clean Code", padrao="brasil")
    assert csv_bytes is not None
    assert len(csv_bytes) > 0
    assert csv_bytes.startswith(b"\xef\xbb\xbf")

    texto_csv = csv_bytes.decode("utf-8-sig")
    assert "Termo Pesquisado" in texto_csv
    assert "Data da Pesquisa" in texto_csv
    assert "Hora da Pesquisa" in texto_csv
    assert ";" in texto_csv
    assert "49,9" in texto_csv


def test_gerar_excel_profissional():
    df = pd.DataFrame([{
        "Título": "Clean Code",
        "Loja": "Google Play Livros",
        "Condição": "Digital",
        "Preço (R$)": 39.90,
        "Link": "https://play.google.com/store/books"
    }])

    excel_bytes = gerar_excel_profissional(df, "Clean Code")
    assert excel_bytes is not None
    assert excel_bytes.startswith(b"PK\x03\x04")


def test_database_operacoes(tmp_path):
    test_db = str(tmp_path / "test_livros.db")
    init_db(db_path=test_db)

    df = pd.DataFrame([{
        "Título": "Duna",
        "Loja": "Amazon BR",
        "Condição": "Novo",
        "Preço (R$)": 59.90,
        "Link": "https://amazon.com.br/duna"
    }])

    salvar_resultados("duna", df, db_path=test_db)
    # Tenta salvar duplicata no mesmo dia (deve ser ignorada)
    salvar_resultados("duna", df, db_path=test_db)

    historico = carregar_historico_termo("duna", db_path=test_db)
    assert len(historico) == 1
    assert historico.iloc[0]["Título"] == "Duna"
    assert historico.iloc[0]["Preço (R$)"] == 59.90


def test_martins_fontes_estrutura():
    from src.scrapers.martins_fontes import coletar_martins_fontes
    # Teste de integração real com termo conhecido
    livros = coletar_martins_fontes("1984")
    assert isinstance(livros, list)
    if livros:
        assert "Título" in livros[0]
        assert "Preço (R$)" in livros[0]
        assert livros[0]["Loja"] == "Martins Fontes"
        assert livros[0]["Condição"] == "Novo"

