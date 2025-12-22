import streamlit as st
import pandas as pd
import numpy as np
import altair as alt 
import os

# --- CONFIGURAÇÕES E CONSTANTES ---
SEP = ';'
ENCODING = 'utf-8-sig'
PATH_ENTRADA = 'inventario_entrada.csv'
PATH_SAIDA = 'inventario_saida.csv'
PATH_PENDENTE = 'acompanhamento_inventario_pendente_baixa.csv'

# --- UTILITÁRIOS ---
def formata_moeda(valor, simbolo_moeda='R$'):
    if pd.isna(valor) or valor is None:
        return 'R$ 0,00'
    try:
        return f'{simbolo_moeda} {valor:,.2f}'.replace(',', 'x').replace('.', ',').replace('x', '.')
    except:
        return 'Valor Inválido'

# --- CAMADA DE ACESSO A DADOS (DATA ACCESS LAYER) ---
@st.cache_data
def load_data(file_path, tipo=None):
    if not os.path.exists(file_path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, sep=SEP, encoding=ENCODING, decimal=',')
        
        # NORMALIZAÇÃO DE SCHEMA
        df.columns = [c.lower() for c in df.columns]
        
        # Conversão de Datas
        col_data = f'dtmov_{tipo}' if tipo else 'data_atualizacao'
        if col_data in df.columns:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
        
        # Tipagem de Filial e Numéricos
        if 'codfilial' in df.columns: df['codfilial'] = df['codfilial'].astype(str)
        if 'filial' in df.columns: df['filial'] = df['filial'].astype(str)
        
        for col in df.columns:
            if 'vlr' in col or 'valor' in col or 'qtd' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {file_path}: {e}")
        return pd.DataFrame()

# --- VISUALIZAÇÃO ---
def create_top_n_chart(df: pd.DataFrame, value_col: str, title: str, color: str):
    if df.empty or value_col not in df.columns:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Sem dados")

    df_grouped = df.groupby(['nome_produto'])[value_col].sum().reset_index()
    df_top_n = df_grouped.nlargest(10, value_col)
    
    chart = alt.Chart(df_top_n).mark_bar(color=color).encode(
        y=alt.Y('nome_produto:N', sort='-x', title='Produto'),
        x=alt.X(f'{value_col}:Q', title='Valor (R$)', axis=alt.Axis(format='$.2s')),
        tooltip=['nome_produto', alt.Tooltip(value_col, format=',.2f')]
    ).properties(title=title, height=350)
    
    return chart.interactive()

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Gestão de Inventário Sênior", layout="wide")
    st.title("📊 BI - Acompanhamento de Inventário Segregado")

    # Carga de Dados
    df_ent = load_data(PATH_ENTRADA, 'entrada')
    df_sai = load_data(PATH_SAIDA, 'saida')
    df_pen = load_data(PATH_PENDENTE)

    # 1. Filtros Globais
    st.sidebar.header("Filtros Operacionais")
    f_ent = df_ent['codfilial'].unique().tolist() if not df_ent.empty else []
    f_sai = df_sai['codfilial'].unique().tolist() if not df_sai.empty else []
    list_filiais = sorted(list(set(f_ent) | set(f_sai)))
    
    sel_filial = st.sidebar.selectbox("Filial", options=["Todas"] + list_filiais)

    # Lógica de Filtragem
    def aplicar_filtro(df, col):
        if df.empty or sel_filial == "Todas": return df
        return df[df[col] == sel_filial].copy()

    df_ent_f = aplicar_filtro(df_ent, 'codfilial')
    df_sai_f = aplicar_filtro(df_sai, 'codfilial')
    df_pen_f = aplicar_filtro(df_pen, 'filial')

    # --- LAYOUT ---
    
    # 1. KPIs Pendentes
    if not df_pen_f.empty:
        st.subheader("⚠️ Inventários Pendentes de Baixa")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Pendente", formata_moeda(df_pen_f['valor'].sum()))
        k2.metric("Notas em Aberto", len(df_pen_f))
        k3.metric("Filiais Ativas", df_pen_f['filial'].nunique())
        
        with st.expander("Ver Detalhes dos Inventários Pendentes"):
            df_p_disp = df_pen_f.copy()
            df_p_disp['valor'] = df_p_disp['valor'].apply(formata_moeda)
            st.dataframe(df_p_disp, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. Séries Temporais com Labels de Valor
    st.header("📈 Evolução das Movimentações")
    c1, c2 = st.columns(2)

    with c1:
        if not df_ent_f.empty and 'dtmov_entrada' in df_ent_f.columns:
            df_ent_f['mes_ano'] = df_ent_f['dtmov_entrada'].dt.to_period('M').astype(str)
            ds_e = df_ent_f.groupby('mes_ano')['vlr_entrada'].sum().reset_index()
            
            # Gráfico de Barras
            base_e = alt.Chart(ds_e).encode(
                x=alt.X('mes_ano:O', title='Mês/Ano'),
                y=alt.Y('vlr_entrada:Q', title='Valor Total')
            )
            
            bars_e = base_e.mark_bar(color='#1f77b4')
            
            # Adição de Labels (Texto)
            labels_e = base_e.mark_text(
                align='center',
                baseline='bottom',
                dy=-5,  # Afasta o texto do topo da barra
                color='#1f77b4'
            ).encode(
                text=alt.Text('vlr_entrada:Q', format='.2s') # Formato compacto (ex: 2.5M)
            )
            
            st.altair_chart((bars_e + labels_e).properties(title="Entradas (EI)"), use_container_width=True)

    with c2:
        if not df_sai_f.empty and 'dtmov_saida' in df_sai_f.columns:
            df_sai_f['mes_ano'] = df_sai_f['dtmov_saida'].dt.to_period('M').astype(str)
            ds_s = df_sai_f.groupby('mes_ano')['vlr_saida'].sum().reset_index()
            
            # Gráfico de Barras
            base_s = alt.Chart(ds_s).encode(
                x=alt.X('mes_ano:O', title='Mês/Ano'),
                y=alt.Y('vlr_saida:Q', title='Valor Total')
            )
            
            bars_s = base_s.mark_bar(color='#d62728')
            
            # Adição de Labels (Texto)
            labels_s = base_s.mark_text(
                align='center',
                baseline='bottom',
                dy=-5,
                color='#d62728'
            ).encode(
                text=alt.Text('vlr_saida:Q', format='.2s')
            )
            
            st.altair_chart((bars_s + labels_s).properties(title="Saídas (SI)"), use_container_width=True)

    # 3. Detalhamento em Abas
    st.markdown("---")
    t_ent, t_sai = st.tabs(["📥 Detalhe Entradas (EI)", "📤 Detalhe Saídas (SI)"])

    with t_ent:
        if not df_ent_f.empty:
            df_e_d = df_ent_f.copy()
            if 'dtmov_entrada' in df_e_d.columns:
                df_e_d['dtmov_entrada'] = df_e_d['dtmov_entrada'].dt.strftime('%d/%m/%Y')
            df_e_d['vlr_entrada'] = df_e_d['vlr_entrada'].apply(formata_moeda)
            st.dataframe(df_e_d, use_container_width=True, hide_index=True)

    with t_sai:
        if not df_sai_f.empty:
            df_s_d = df_sai_f.copy()
            if 'dtmov_saida' in df_s_d.columns:
                df_s_d['dtmov_saida'] = df_s_d['dtmov_saida'].dt.strftime('%d/%m/%Y')
            df_s_d['vlr_saida'] = df_s_d['vlr_saida'].apply(formata_moeda)
            st.dataframe(df_s_d, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()