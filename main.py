import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

from src.core.config import CORES_LOJAS
from src.database import (
    init_db,
    salvar_resultados,
    carregar_historico_termo,
    carregar_evolucao_precos,
    listar_termos_buscados
)
from src.scrapers import (
    buscar_metadados_google_books,
    coletar_todas_as_lojas_paralelo
)
from src.services import (
    gerar_csv_profissional,
    gerar_excel_profissional
)

init_db()

st.set_page_config(
    page_title="Ayato Livrarias | Comparador de Preços",
    page_icon="🐸",
    layout="wide"
)

# Inicialização do st.session_state para manter a interface viva
if "resultados" not in st.session_state:
    st.session_state["resultados"] = None
if "livro_info" not in st.session_state:
    st.session_state["livro_info"] = None
if "termo_buscado" not in st.session_state:
    st.session_state["termo_buscado"] = ""
if "status_lojas" not in st.session_state:
    st.session_state["status_lojas"] = {}

# Estilização visual moderna com tons verde-claro e azul
st.markdown(
    """
    <style>
        /* Cards de métricas com fundo suave verde-água/azul */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #F0FDF4 0%, #F0F9FF 100%);
            border: 1px solid #BAE6FD;
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.05);
        }

        div[data-testid="stMetricLabel"] p {
            color: #0369A1 !important;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: #0F172A !important;
        }

        /* Botão principal com gradiente azul para verde claro */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0284C7 0%, #10B981 100%);
            border: none;
            color: white;
            font-weight: 600;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.2);
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"]:hover {
            opacity: 0.93;
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
        }

        /* Botão de download em tom verde menta */
        div.stDownloadButton > button {
            background: #F0FDF4;
            border: 1px solid #10B981;
            color: #047857;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        div.stDownloadButton > button:hover {
            background: #D1FAE5;
            color: #065F46;
            border-color: #059669;
        }

        /* Card Hero da Oferta Campeã */
        .card-campeao {
            background: linear-gradient(135deg, #ECFDF5 0%, #F0F9FF 100%);
            border: 2px solid #34D399;
            border-radius: 16px;
            padding: 22px 26px;
            margin-bottom: 20px;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.12);
        }

        .badge-campeao {
            display: inline-block;
            background: #10B981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        /* Card de Destaque por Loja */
        .card-loja-individual {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
            height: 100%;
        }

        /* Barra lateral */
        section[data-testid="stSidebar"] {
            background-color: #F8FCFA;
            border-right: 1px solid #E2E8F0;
        }

        /* Hero informativo inicial */
        .hero-banner {
            background: linear-gradient(135deg, #F0FDF4 0%, #E0F2FE 100%);
            border: 1px solid #BAE6FD;
            border-radius: 16px;
            padding: 24px;
            margin-top: 10px;
            margin-bottom: 24px;
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🐸 📖 Ayato Livrarias")
st.caption("Comparador inteligente em tempo real: Estante Virtual, Martins Fontes, Magazine Luiza, Buscapé, Google Play Livros, Amazon BR e Mercado Livre.")


@st.cache_data(ttl=300, show_spinner=False)
def buscar_ofertas_com_cache(termo: str) -> tuple[dict | None, list[dict], dict[str, int]]:
    """
    Executa busca em paralelo com cache de 5 minutos (TTL=300s).
    Evita bloqueios de taxa (rate-limits) e acelera consultas repetidas.
    """
    info = buscar_metadados_google_books(termo)
    # Busca ampla por título em todas as lojas para garantir dezenas de ofertas
    # (evita limitar a busca ao código de barras/ISBN de uma única tiragem específica)
    resultados, status = coletar_todas_as_lojas_paralelo(termo)
    return info, resultados, status


def executar_pesquisa(termo_busca: str, forcar_atualizacao: bool = False):
    """Executa a coleta de metadados e preços com suporte a cache."""
    termo_limpo = termo_busca.strip()
    if not termo_limpo:
        st.warning("Por favor, digite um título válido para pesquisar.")
        return

    if forcar_atualizacao:
        buscar_ofertas_com_cache.clear()

    with st.spinner(f"🐸 Consultando lojas em tempo real para '{termo_limpo}'..."):
        livro_info, resultados, status_lojas = buscar_ofertas_com_cache(termo_limpo)

        st.session_state["resultados"] = resultados
        st.session_state["livro_info"] = livro_info
        st.session_state["termo_buscado"] = termo_limpo
        st.session_state["status_lojas"] = status_lojas

        if resultados:
            df_raw = pd.DataFrame(resultados).drop_duplicates(subset=["Título", "Loja", "Preço (R$)"])
            salvar_resultados(termo_limpo, df_raw)


# --- BARRA LATERAL (FILTROS E HISTÓRICO) ---
with st.sidebar:
    st.header("⚙️ Filtros da Pesquisa")
    filtro_condicao = st.multiselect(
        "Condição do Livro:",
        options=["Novo", "Usado", "Digital"],
        default=["Novo", "Usado", "Digital"]
    )

    lojas_disponiveis = list(CORES_LOJAS.keys())
    filtro_lojas = st.multiselect(
        "Lojas Selecionadas:",
        options=lojas_disponiveis,
        default=lojas_disponiveis
    )

    forcar_cache = st.checkbox("🔄 Forçar atualização sem cache", value=False, help="Ignora dados salvos em memória nos últimos 10 minutos.")

    st.divider()
    st.header("📜 Histórico de Preços")
    termos_recentes = listar_termos_buscados()
    termo_hist = st.text_input("Consultar histórico por termo:", placeholder="Ex: Clean Code, Duna...")

    if termos_recentes:
        termo_sel = st.selectbox("Ou selecione uma busca recente:", options=[""] + termos_recentes, index=0)
        if termo_sel:
            termo_hist = termo_sel

    if st.button("Carregar Histórico"):
        if termo_hist.strip():
            df_hist = carregar_historico_termo(termo_hist)
            if not df_hist.empty:
                st.subheader(f"Histórico: {termo_hist}")
                st.dataframe(df_hist, hide_index=True)

                df_evolucao = carregar_evolucao_precos(termo_hist)
                if not df_evolucao.empty and len(df_evolucao) > 1:
                    st.caption("Evolução do menor preço por data:")
                    chart_hist = alt.Chart(df_evolucao).mark_line(point=True).encode(
                        x=alt.X("Data:T", title="Data"),
                        y=alt.Y("Menor Preço (R$):Q", title="Menor Preço (R$)"),
                        color=alt.Color("Loja:N", title="Loja"),
                        tooltip=["Data", "Loja", "Menor Preço (R$)", "Preço Médio (R$)", "Ofertas"]
                    ).properties(height=220)
                    st.altair_chart(chart_hist, use_container_width=True)
            else:
                st.info(f"Nenhum histórico encontrado para '{termo_hist}'.")

# --- ÁREA PRINCIPAL DE PESQUISA ---
col_input, col_btn = st.columns([5, 1])
with col_input:
    termo_digitado = st.text_input(
        "Digite o título do livro ou autor:",
        placeholder="Ex: Clean Code, O Pequeno Príncipe, Duna, Sapiens...",
        value=st.session_state["termo_buscado"]
    )
with col_btn:
    st.write("")
    st.write("")
    botao_buscar = st.button("Buscar Ofertas", type="primary", use_container_width=True)

if botao_buscar:
    executar_pesquisa(termo_digitado, forcar_atualizacao=forcar_cache)
    st.rerun()

# --- HERO SECTION INICIAL ---
if st.session_state["resultados"] is None:
    st.markdown(
        """
        <div class="hero-banner">
            <h2 style="color: #0369A1; margin-bottom: 8px;">Economize nas melhores livrarias do Brasil 📚</h2>
            <p style="color: #334155; font-size: 1.05rem; margin-bottom: 18px;">
                Rastreamos simultaneamente na <strong>Estante Virtual</strong>, <strong>Martins Fontes</strong>, 
                <strong>Magazine Luiza</strong>, <strong>Buscapé</strong>, <strong>Amazon BR</strong> e <strong>Google Play Livros</strong> em segundos.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("##### 💡 Ou clique em um livro popular para testar agora:")
    sugestoes = ["Clean Code", "O Pequeno Príncipe", "Duna", "Sapiens", "Hábitos Atômicos", "1984"]
    cols_sug = st.columns(len(sugestoes))
    for i, sug in enumerate(sugestoes):
        if cols_sug[i].button(f"📖 {sug}", use_container_width=True):
            executar_pesquisa(sug, forcar_atualizacao=forcar_cache)
            st.rerun()

# --- EXIBIÇÃO COMPLETA DOS RESULTADOS ---
if st.session_state["resultados"] is not None:
    resultados = st.session_state["resultados"]
    livro_info = st.session_state["livro_info"]
    status_lojas = st.session_state["status_lojas"]
    termo_atual = st.session_state["termo_buscado"]

    # 1. Metadados do Livro Identificado
    if livro_info:
        st.success("Livro identificado com precisão!")
        c_capa, c_info = st.columns([1, 5])
        with c_capa:
            if livro_info.get("capa"):
                st.image(livro_info["capa"], width=120)
            else:
                st.info("Sem capa disponível")
        with c_info:
            st.subheader(livro_info.get("titulo", termo_atual))
            subtitulo = f" - *{livro_info['subtitulo']}*" if livro_info.get("subtitulo") else ""
            st.markdown(f"**Autor(es):** {livro_info.get('autores')} | **Publicação:** {livro_info.get('publicado')}{subtitulo}")
            if livro_info.get("isbn"):
                st.markdown(f"🎯 **ISBN Identificado (Edição Exata):** `{livro_info['isbn']}`")
            if livro_info.get("descricao") and livro_info["descricao"] != "Sem descrição disponível.":
                desc_curta = (livro_info["descricao"][:250] + "...") if len(livro_info["descricao"]) > 250 else livro_info["descricao"]
                st.caption(f"Sinopse: {desc_curta}")
        st.divider()

    # 2. Resumo de Retorno por Loja
    if status_lojas:
        cols_st = st.columns(len(status_lojas))
        for idx, (loja, qtd) in enumerate(status_lojas.items()):
            with cols_st[idx]:
                cores = CORES_LOJAS.get(loja, {"bg": "#E0F2FE", "text": "#0369A1", "border": "#BAE6FD"})
                if qtd > 0:
                    st.metric(label=loja, value=f"{qtd} ofertas")
                else:
                    st.metric(label=loja, value="Sem retorno")

    if not resultados:
        st.warning(f"Nenhuma oferta relevante encontrada para '{termo_atual}'. Tente simplificar o termo.")
    else:
        df = pd.DataFrame(resultados).drop_duplicates(subset=["Título", "Loja", "Preço (R$)"]).reset_index(drop=True)

        # Simulação de frete
        with st.expander("🚚 Calculadora e Informações sobre Frete", expanded=False):
            st.info(
                "💡 **Aviso:** Os preços exibidos são os valores de vitrine do produto. "
                "Produtos digitais (Google Play Livros) possuem **frete R$ 0,00**. "
                "Para livros físicos (Mercado Livre, Estante Virtual, Travessa), o frete varia com o seu CEP."
            )
            simular_frete = st.checkbox("Simular frete fixo estimado para livros físicos", value=False)
            frete_valor = 0.0
            if simular_frete:
                frete_valor = st.number_input("Valor estimado do frete (R$):", min_value=0.0, value=15.00, step=1.0)
                df["Preço c/ Frete (R$)"] = df.apply(
                    lambda r: r["Preço (R$)"] if r["Condição"] == "Digital" else r["Preço (R$)"] + frete_valor,
                    axis=1
                ).round(2)

        # Aplicar filtros da barra lateral (Condição e Loja)
        df_filtrado = df[
            (df["Condição"].isin(filtro_condicao)) &
            (df["Loja"].isin(filtro_lojas))
        ].sort_values(by="Preço (R$)", ascending=True).reset_index(drop=True)

        if df_filtrado.empty:
            st.info("Nenhuma oferta disponível para os filtros selecionados na barra lateral.")
        else:
            menor_preco = df_filtrado["Preço (R$)"].min()
            maior_preco = df_filtrado["Preço (R$)"].max()
            livro_campeao = df_filtrado.loc[df_filtrado["Preço (R$)"].idxmin()]
            preco_medio = df_filtrado["Preço (R$)"].mean()
            economia_reais = maior_preco - menor_preco
            economia_pct = (economia_reais / maior_preco * 100) if maior_preco > 0 else 0

            # --- CARD DESTAQUE: OFERTA CAMPEÃ ---
            cores_loja_campea = CORES_LOJAS.get(livro_campeao["Loja"], {"bg": "#FEF08A", "text": "#854D0E", "border": "#FACC15"})
            
            st.markdown(
                f"""
                <div class="card-campeao">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span class="badge-campeao">🏆 OFERTA CAMPEÃ</span>
                            <span style="display: inline-block; padding: 4px 10px; margin-left: 6px; border-radius: 12px; font-size: 0.82rem; font-weight: 700; background: {cores_loja_campea['bg']}; color: {cores_loja_campea['text']}; border: 1px solid {cores_loja_campea['border']};">
                                {livro_campeao['Loja']}
                            </span>
                            <span style="display: inline-block; padding: 4px 10px; margin-left: 4px; border-radius: 12px; font-size: 0.82rem; font-weight: 600; background: #E2E8F0; color: #475569;">
                                {livro_campeao['Condição']}
                            </span>
                            <h3 style="margin: 10px 0 4px 0; color: #0F172A;">{livro_campeao['Título']}</h3>
                            <p style="margin: 0; color: #047857; font-weight: 600; font-size: 0.95rem;">
                                💸 Economia de até <strong>R$ {economia_reais:.2f} ({economia_pct:.0f}%)</strong> em relação à oferta mais cara!
                            </p>
                        </div>
                        <div style="text-align: right; min-width: 170px; margin-top: 6px;">
                            <span style="font-size: 0.85rem; color: #64748B;">A partir de</span>
                            <div style="font-size: 2.3rem; font-weight: 800; color: #047857; line-height: 1.1;">
                                R$ {menor_preco:.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.link_button(
                f"👉 Acessar Oferta Campeã no {livro_campeao['Loja']} (R$ {menor_preco:.2f})",
                livro_campeao["Link"],
                type="primary",
                use_container_width=True
            )

            st.write("")

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🏆 Melhor Preço", f"R$ {menor_preco:.2f}", f"{livro_campeao['Loja']} ({livro_campeao['Condição']})")
            with m2:
                st.metric("📊 Preço Médio", f"R$ {preco_medio:.2f}")
            with m3:
                st.metric("📚 Ofertas Disponíveis", len(df_filtrado))

            st.divider()

            # --- NAVEGAÇÃO POR ABAS (TABS) ---
            tab_tabela, tab_lojas, tab_graficos = st.tabs([
                "📋 Todas as Ofertas",
                "🏪 Comparativo por Loja",
                "📊 Gráficos & Estatísticas"
            ])

            # ABA 1: TABELA COMPLETA COM FILTRO RÁPIDO E EXPORTAÇÃO
            with tab_tabela:
                col_busca_tabela, col_ordena = st.columns([3, 2])
                with col_busca_tabela:
                    busca_interna = st.text_input("🔍 Filtrar palavras nos resultados:", placeholder="Ex: capa dura, edição...")
                with col_ordena:
                    criterio_ordenar = st.selectbox(
                        "Ordenar resultados por:",
                        options=["Menor Preço", "Maior Preço", "Loja (A-Z)", "Título (A-Z)"]
                    )

                df_tabela = df_filtrado.copy()
                if busca_interna.strip():
                    df_tabela = df_tabela[df_tabela["Título"].str.contains(busca_interna, case=False, na=False)]

                if criterio_ordenar == "Menor Preço":
                    df_tabela = df_tabela.sort_values(by="Preço (R$)", ascending=True)
                elif criterio_ordenar == "Maior Preço":
                    df_tabela = df_tabela.sort_values(by="Preço (R$)", ascending=False)
                elif criterio_ordenar == "Loja (A-Z)":
                    df_tabela = df_tabela.sort_values(by="Loja", ascending=True)
                elif criterio_ordenar == "Título (A-Z)":
                    df_tabela = df_tabela.sort_values(by="Título", ascending=True)

                col_config = {
                    "Preço (R$)": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                    "Link": st.column_config.LinkColumn("Link Direto", display_text="Acessar Oferta"),
                    "Loja": st.column_config.TextColumn("Loja"),
                    "Condição": st.column_config.TextColumn("Condição")
                }
                if "Preço c/ Frete (R$)" in df_tabela.columns:
                    col_config["Preço c/ Frete (R$)"] = st.column_config.NumberColumn("Preço c/ Frete", format="R$ %.2f")

                st.dataframe(
                    df_tabela,
                    column_config=col_config,
                    use_container_width=True,
                    hide_index=True
                )

                st.write("")
                # Exportação CSV e Excel Padronizados
                with st.expander("📥 Exportar Relatório (CSV e Excel)", expanded=True):
                    col_opt, col_btns = st.columns([3, 3])
                    
                    with col_opt:
                        tipo_padrao = st.radio(
                            "Padrão do arquivo CSV:",
                            options=[
                                "Excel Brasil (Separador ';' e Decimal ',')",
                                "Padrão Internacional / Power BI (Separador ',' e Decimal '.')"
                            ],
                            index=0
                        )

                    padrao_escolhido = "brasil" if "Brasil" in tipo_padrao else "internacional"
                    dados_csv_bytes = gerar_csv_profissional(df_tabela, termo_atual, padrao=padrao_escolhido)
                    dados_excel_bytes = gerar_excel_profissional(df_tabela, termo_atual)

                    agora_dt = datetime.now()
                    data_arquivo = agora_dt.strftime("%d-%m-%Y_%Hh%M")
                    slug_termo = termo_atual.lower().replace(" ", "_")
                    nome_csv = f"comparativo_{slug_termo}_{data_arquivo}.csv"
                    nome_excel = f"comparativo_{slug_termo}_{data_arquivo}.xlsx"

                    with col_btns:
                        st.download_button(
                            label="📥 Baixar em CSV (Excel Brasil / Power BI)",
                            data=dados_csv_bytes,
                            file_name=nome_csv,
                            mime="text/csv; charset=utf-8-sig",
                            use_container_width=True
                        )
                        st.download_button(
                            label="📊 Baixar Planilha Formatada (.xlsx)",
                            data=dados_excel_bytes,
                            file_name=nome_excel,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                    st.caption(
                        f"🗓️ **Data do Relatório:** {agora_dt.strftime('%d/%m/%Y às %H:%M:%S')} | "
                        "💡 **Dica Excel:** No arquivo CSV, se a data ou valores aparecerem como `######`, basta dar um duplo clique na divisória da coluna para expandi-la, ou utilize a **Planilha Formatada (.xlsx)** que já vem com as colunas autoajustadas."
                    )

            # ABA 2: COMPARATIVO LADO A LADO POR LOJA
            with tab_lojas:
                st.markdown("#### Melhores ofertas de cada loja lado a lado:")
                lojas_presentes = df_filtrado["Loja"].unique().tolist()

                if not lojas_presentes:
                    st.info("Nenhuma loja disponível nos filtros atuais.")
                else:
                    cols_lojas_cards = st.columns(len(lojas_presentes))
                    for idx, loja_nome in enumerate(lojas_presentes):
                        df_loja = df_filtrado[df_filtrado["Loja"] == loja_nome].sort_values(by="Preço (R$)", ascending=True)
                        melhor_da_loja = df_loja.iloc[0]
                        cores = CORES_LOJAS.get(loja_nome, {"bg": "#E0F2FE", "text": "#0369A1", "border": "#BAE6FD"})

                        with cols_lojas_cards[idx]:
                            st.markdown(
                                f"""
                                <div class="card-loja-individual">
                                    <div style="background: {cores['bg']}; color: {cores['text']}; border: 1px solid {cores['border']}; border-radius: 8px; padding: 6px; font-weight: 700; font-size: 0.9rem; margin-bottom: 10px;">
                                        {loja_nome}
                                    </div>
                                    <div style="font-size: 1.8rem; font-weight: 800; color: #0F172A; margin: 4px 0;">
                                        R$ {melhor_da_loja['Preço (R$)']:.2f}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 8px;">
                                        Condição: <strong>{melhor_da_loja['Condição']}</strong> ({len(df_loja)} opções)
                                    </div>
                                    <p style="font-size: 0.85rem; color: #334155; height: 42px; overflow: hidden; margin-bottom: 12px;" title="{melhor_da_loja['Título']}">
                                        {melhor_da_loja['Título'][:55]}...
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            st.link_button(
                                f"Acessar no {loja_nome}",
                                melhor_da_loja["Link"],
                                use_container_width=True
                            )

                    st.divider()
                    st.markdown("#### Preço Médio por Loja:")
                    df_media_loja = df_filtrado.groupby("Loja")["Preço (R$)"].mean().reset_index()
                    df_media_loja["Preço Médio (R$)"] = df_media_loja["Preço (R$)"].round(2)

                    chart_bar = alt.Chart(df_media_loja).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                        x=alt.X("Loja:N", title="Loja"),
                        y=alt.Y("Preço Médio (R$):Q", title="Preço Médio (R$)"),
                        color=alt.Color("Loja:N", legend=None),
                        tooltip=["Loja", "Preço Médio (R$)"]
                    ).properties(height=260)
                    st.altair_chart(chart_bar, use_container_width=True)

            # ABA 3: ANÁLISE GRÁFICA & ESTATÍSTICAS
            with tab_graficos:
                st.markdown("#### Dispersão de Preços por Loja e Condição")
                chart_disp = alt.Chart(df_filtrado).mark_circle(size=120).encode(
                    x=alt.X("Preço (R$):Q", title="Preço (R$)"),
                    y=alt.Y("Loja:N", title="Loja"),
                    color=alt.Color(
                        "Condição:N",
                        title="Condição",
                        scale=alt.Scale(
                            domain=["Novo", "Usado", "Digital"],
                            range=["#0284C7", "#10B981", "#06B6D4"]
                        )
                    ),
                    tooltip=["Título", "Preço (R$)", "Loja", "Condição"]
                ).properties(height=320).interactive()
                st.altair_chart(chart_disp, use_container_width=True)

                st.divider()
                st.markdown("#### Resumo Estatístico")
                resumo_est = df_filtrado.groupby(["Loja", "Condição"])["Preço (R$)"].agg(
                    Mínimo="min",
                    Médio="mean",
                    Máximo="max",
                    Ofertas="count"
                ).reset_index()
                resumo_est["Médio"] = resumo_est["Médio"].round(2)
                st.dataframe(resumo_est, hide_index=True, use_container_width=True)
