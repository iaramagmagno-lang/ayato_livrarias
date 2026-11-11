import io
import pandas as pd
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def gerar_csv_profissional(df: pd.DataFrame, termo: str, padrao: str = "brasil") -> bytes:
    """
    Gera um relatório CSV estruturado com data/hora ajustadas e compatibilidade total com Excel.
    """
    if df.empty:
        return b""

    df_export = df.copy()
    agora = datetime.now()
    menor_p = df_export["Preço (R$)"].min()

    df_export["Termo Pesquisado"] = termo
    df_export["Data da Pesquisa"] = agora.strftime("%d/%m/%Y")
    df_export["Hora da Pesquisa"] = agora.strftime("%H:%M:%S")
    df_export["Diferença p/ Menor (R$)"] = (df_export["Preço (R$)"] - menor_p).round(2)

    colunas_finais = [
        "Termo Pesquisado",
        "Título",
        "Loja",
        "Condição",
        "Preço (R$)",
        "Diferença p/ Menor (R$)",
        "Link",
        "Data da Pesquisa",
        "Hora da Pesquisa"
    ]
    df_export = df_export[[c for c in colunas_finais if c in df_export.columns]]
    df_export = df_export.rename(columns={
        "Título": "Título do Livro",
        "Loja": "Loja / Marketplace",
        "Condição": "Condição",
        "Link": "Link Direto da Oferta"
    })

    if padrao == "brasil":
        return df_export.to_csv(
            index=False,
            sep=";",
            decimal=",",
            encoding="utf-8-sig"
        ).encode("utf-8-sig")
    else:
        return df_export.to_csv(
            index=False,
            sep=",",
            decimal=".",
            encoding="utf-8-sig"
        ).encode("utf-8-sig")


def gerar_excel_profissional(df: pd.DataFrame, termo: str) -> bytes:
    """
    Gera planilha Excel (.xlsx) com formatação executiva, moedas e colunas autoajustadas.
    """
    if df.empty:
        return b""

    df_export = df.copy()
    agora = datetime.now()
    menor_p = df_export["Preço (R$)"].min()

    df_export["Termo Pesquisado"] = termo
    df_export["Data da Pesquisa"] = agora.strftime("%d/%m/%Y")
    df_export["Hora da Pesquisa"] = agora.strftime("%H:%M:%S")
    df_export["Diferença p/ Menor (R$)"] = (df_export["Preço (R$)"] - menor_p).round(2)

    colunas_ordenadas = [
        "Termo Pesquisado",
        "Título",
        "Loja",
        "Condição",
        "Preço (R$)",
        "Diferença p/ Menor (R$)",
        "Link",
        "Data da Pesquisa",
        "Hora da Pesquisa"
    ]
    df_export = df_export[[c for c in colunas_ordenadas if c in df_export.columns]]
    df_export = df_export.rename(columns={
        "Título": "Título do Livro",
        "Loja": "Loja / Marketplace",
        "Condição": "Condição",
        "Link": "Link Direto da Oferta"
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, sheet_name="Comparativo", index=False)
        worksheet = writer.sheets["Comparativo"]

        header_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        border_thin = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0")
        )

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for row in worksheet.iter_rows(min_row=2):
            for cell in row:
                cell.border = border_thin
                if cell.column in [5, 6]:
                    cell.number_format = 'R$ #,##0.00'
                    cell.alignment = Alignment(horizontal="right")
                elif cell.column == 7:
                    cell.font = Font(color="0284C7", underline="single")

        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    return output.getvalue()

