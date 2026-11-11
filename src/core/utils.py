import re
import unicodedata
from src.core.config import STOP_WORDS, TERMOS_BLOQUEADOS


def remover_acentos(texto: str) -> str:
    """Remove acentuação e caracteres especiais mantendo ASCII limpo."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )


def simplificar_termo_busca(termo: str) -> str:
    """
    Remove subtítulos longos (após ':' ou '-'), parênteses e caracteres
    especiais que costumam zerar os resultados em e-commerces.
    Ex: 'Clean Code: A Handbook of Agile Software Craftsmanship' -> 'Clean Code'
    """
    termo_limpo = re.split(r"[:\-\(]", termo)[0].strip()
    return termo_limpo if len(termo_limpo) >= 3 else termo.strip()


def eh_relevante(titulo_item: str, termo_busca: str) -> bool:
    """
    Filtra itens irrelevantes (camisetas, canecas, adesivos) e garante que
    ao menos parte das palavras-chave pesquisadas constem no título retornado.
    """
    titulo_norm = remover_acentos(titulo_item.lower())
    termo_norm = remover_acentos(termo_busca.lower())

    for bloq in TERMOS_BLOQUEADOS:
        if bloq in titulo_norm and bloq not in termo_norm:
            return False

    palavras_busca = [
        p for p in re.findall(r"\w+", termo_norm)
        if p not in STOP_WORDS and len(p) >= 2
    ]
    if not palavras_busca:
        return True

    encontradas = sum(1 for p in palavras_busca if p in titulo_norm)
    return (encontradas / len(palavras_busca)) >= 0.5

