# 🐸 📖 Ayato Livrarias

> Comparador de preços de livros em tempo real para o mercado brasileiro, integrando **Google Play Livros**, **Mercado Livre**, **Estante Virtual**, **Amazon BR** e **Livraria da Travessa**.

---

## 🏗️ Estrutura Arquitetural do Projeto

O projeto adota uma arquitetura modular limpa e escalável baseada no padrão de camadas (`src/`):

```text
Ayapo Livrarias/
│
├── main.py                    # Ponto de entrada (UI e visualização Streamlit)
├── requirements.txt           # Dependências do projeto
├── pytest.ini                 # Configurações de execução dos testes
├── README.md                  # Documentação do projeto
│
├── .streamlit/
│   └── config.toml            # Tema nativo (paleta de tons verdes claros e azuis)
│
├── data/
│   └── precos_livros.db       # Banco de dados SQLite persistente
│
├── src/
│   ├── core/
│   │   ├── config.py          # Configurações globais, caminhos e paletas das lojas
│   │   └── utils.py           # Normalização de texto, remoção de acentos e filtro de relevância
│   │
│   ├── database/
│   │   └── db_manager.py      # Gestor do banco de dados (SQLite, deduplicação e histórico)
│   │
│   ├── scrapers/              # Módulos isolados de raspagem e APIs
│   │   ├── google_books.py    # API oficial Google Books e Google Play Livros
│   │   ├── mercadolivre.py    # Scraping Mercado Livre (com suporte a ISBN e Andes UI)
│   │   ├── estante_virtual.py # Scraping Estante Virtual (Next.js data e HTML)
│   │   ├── amazon.py          # Coleta Amazon BR (HTTP leve + fallback Playwright)
│   │   ├── travessa.py        # Coleta Livraria da Travessa
│   │   └── orchestrator.py    # Execução concorrente com ThreadPoolExecutor
│   │
│   └── services/
│       └── exporters.py       # Geradores de relatórios profissionais (CSV e Excel .xlsx)
│
└── tests/
    └── test_scrapers.py       # Suíte de testes automatizados unitários (pytest)
```

---

## 🚀 Como Executar o Projeto

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Inicie o Streamlit:**
   ```bash
   streamlit run main.py
   ```

3. **Acesse no navegador:**  
   `http://localhost:8501`

---

## 🧪 Como Executar os Testes Automatizados

Para rodar os testes unitários de raspadores, banco e exportadores:
```bash
python -m pytest
```

---

## 🌟 Principais Recursos
* **⚡ Coleta Paralela:** 5 lojas consultadas simultaneamente em threads (~3 segundos de resposta).
* **🧠 Cache em Memória:** `@st.cache_data(ttl=600)` para consultas instantâneas em livros já buscados.
* **🎯 Refinamento por ISBN:** Detecção automática do ISBN-13 para garantir a edição exata do livro.
* **🚚 Simulador de Frete:** Cálculo estimado de frete para livros físicos vs digitais (R$ 0 de frete).
* **📊 Exportações Profissionais:**
  * **CSV:** Padrão Brasil com delimitador `;` e codificação UTF-8 com BOM (`utf-8-sig`).
  * **Excel (.xlsx):** Planilha formatada com cabeçalho azul, formatação de moedas e links clicáveis.
* **📜 Histórico Temporal:** Armazenamento automático e gráfico de variação do menor preço ao longo das datas.

