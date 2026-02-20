import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard: Conversão Comercial Mais Sol",
    page_icon="☀️",
    layout="wide",
)

# --- Funções de Carregamento de Dados ---
@st.cache_data
def load_data():
    # 1. Carregar dados de Vendas (DRE) - Fechamentos
    try:
        df_dre = pd.read_excel("DRE_Dezembro Origem Sun Janeiro e Fervereiro.xlsx")
        df_dre['Data'] = pd.to_datetime(df_dre['Data'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar DRE: {e}")
        df_dre = pd.DataFrame()

    # 2. Carregar Propostas em Aberto (Paulo e Claudenia)
    try:
        df_paulo = pd.read_excel("Propostas em aberto sun Paulo.xlsx")
        df_paulo['Data da criação'] = pd.to_datetime(df_paulo['Data da criação'], errors='coerce')
        
        df_clau = pd.read_excel("Propostas em aberto sun CLau.xlsx")
        df_clau['Data da criação'] = pd.to_datetime(df_clau['Data da criação'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar Propostas: {e}")
        df_paulo, df_clau = pd.DataFrame(), pd.DataFrame()

    # 3. Carregar SDR (Aba específica do ficheiro Excel)
    try:
        # Ajuste o nome da aba ('SDR') ou a linha a saltar (skiprows) conforme a estrutura real do seu Excel
        df_sdr = pd.read_excel("KPI Marketing - 2026.xlsx", sheet_name="SDR", skiprows=2) 
    except Exception as e:
        st.error(f"Erro ao carregar SDR: {e}")
        df_sdr = pd.DataFrame()

    return df_dre, df_paulo, df_clau, df_sdr

df_dre, df_paulo, df_clau, df_sdr = load_data()

# --- Filtros da Barra Lateral ---
st.sidebar.image("https://img.icons8.com/color/96/000000/sun--v1.png", width=60) # Ícone de sol placeholder
st.sidebar.header("🔍 Filtros de Análise")

# Filtro de Mês (Focando em Dezembro/2025 e Janeiro/2026)
meses_opcoes = {'Dezembro 2025': (2025, 12), 'Janeiro 2026': (2026, 1), 'Ambos': 'Ambos'}
mes_selecionado = st.sidebar.selectbox("Selecione o Período", list(meses_opcoes.keys()))

# --- Lógica de Filtragem por Data ---
def filtrar_por_mes(df, coluna_data, filtro_mes):
    if df.empty or coluna_data not in df.columns:
        return df
        
    if filtro_mes == 'Ambos':
        return df[(df[coluna_data].dt.year.isin([2025, 2026])) & (df[coluna_data].dt.month.isin([12, 1]))]
    else:
        ano, mes = meses_opcoes[filtro_mes]
        return df[(df[coluna_data].dt.year == ano) & (df[coluna_data].dt.month == mes)]

df_dre_filtrado = filtrar_por_mes(df_dre, 'Data', mes_selecionado)
df_paulo_filtrado = filtrar_por_mes(df_paulo, 'Data da criação', mes_selecionado)
df_clau_filtrado = filtrar_por_mes(df_clau, 'Data da criação', mes_selecionado)

# --- Lógica de Funil Cumulativo ---
def calcular_funil(nome_vendedor, df_propostas, df_vendas):
    vendas = 0
    if not df_vendas.empty and 'Responsável' in df_vendas.columns:
        vendas = df_vendas[df_vendas['Responsável'].str.contains(nome_vendedor, na=False, case=False)].shape[0]
    
    qtd_negociacao_atual = 0
    qtd_proposta_atual = 0
    qtd_agendados_atual = 0
    
    if not df_propostas.empty and 'Estágio do Processo' in df_propostas.columns:
        status_counts = df_propostas['Estágio do Processo'].value_counts()
        qtd_negociacao_atual = status_counts.filter(like='Negociação').sum()
        qtd_proposta_atual = status_counts.filter(like='Proposta').sum()
        qtd_agendados_atual = status_counts.filter(like='Agendados
