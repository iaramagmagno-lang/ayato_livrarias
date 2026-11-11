import os

# Caminho para o banco de dados dentro da pasta data/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "precos_livros.db")

# Paleta oficial de cores para badges de lojas
CORES_LOJAS = {
    "Mercado Livre": {"bg": "#FEF08A", "text": "#854D0E", "border": "#FACC15"},
    "Amazon BR": {"bg": "#FFEDD5", "text": "#9A3412", "border": "#FB923C"},
    "Estante Virtual": {"bg": "#DBEAFE", "text": "#1E40AF", "border": "#93C5FD"},
    "Google Play Livros": {"bg": "#CCFBF1", "text": "#0F766E", "border": "#5EEAD4"},
    "Livraria da Travessa": {"bg": "#FEE2E2", "text": "#991B1B", "border": "#FCA5A5"}
}

# Stop words e termos irrelevantes para o filtro de relevância
STOP_WORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da",
    "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "com",
    "sem", "sob", "sobre", "e", "ou", "livro", "livros", "edicao", "ed",
    "volume", "vol"
}

TERMOS_BLOQUEADOS = {
    "camiseta", "camisa", "caneca", "adesivo", "poster", "quadro",
    "moletom", "almofada", "marcador de pagina", "porta copo", "chaveiro",
    "capinha", "mousepad"
}

