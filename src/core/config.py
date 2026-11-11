import os

# Caminho para o banco de dados dentro da pasta data/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "precos_livros.db")

# Paleta oficial de cores para badges de lojas ativas
CORES_LOJAS = {
    "Magazine Luiza": {"bg": "#E0F2FE", "text": "#0284C7", "border": "#38BDF8"},
    "Estante Virtual": {"bg": "#DBEAFE", "text": "#1E40AF", "border": "#93C5FD"},
    "Martins Fontes": {"bg": "#F3E8FF", "text": "#6B21A8", "border": "#D8B4FE"},
    "Buscapé": {"bg": "#FEF9C3", "text": "#A16207", "border": "#FDE047"}
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
