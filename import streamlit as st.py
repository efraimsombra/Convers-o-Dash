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
        df_dre = pd.read_csv("DRE_Dezembro Origem Sun Janeiro e Fervereiro.xlsx - Ploomes.csv")
        df_dre['Data'] = pd.to_datetime(df_dre['Data'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar DRE: {e}")
        df_dre = pd.DataFrame()

    # 2. Carregar Propostas em Aberto (Paulo e Claudenia)
    try:
        df_paulo = pd.read_csv("Propostas em aberto sun Paulo.xlsx - Ploomes.csv")
        df_paulo['Data da criação'] = pd.to_datetime(df_paulo['Data da criação'], errors='coerce')
        
        df_clau = pd.read_csv("Propostas em aberto sun CLau.xlsx - Ploomes.csv")
        df_clau['Data da criação'] = pd.to_datetime(df_clau['Data da criação'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar Propostas: {e}")
        df_paulo, df_clau = pd.DataFrame(), pd.DataFrame()

    # 3. Carregar SDR (A estrutura da planilha SDR requer atenção especial nas linhas/colunas)
    # Assumindo a leitura padrão para o exemplo. Pode ser necessário ajustar skiprows.
    try:
        df_sdr = pd.read_csv("KPI Marketing - 2026.xlsx - SDR.csv", skiprows=2) 
    except Exception as e:
        st.error(f"Erro ao carregar SDR: {e}")
        df_sdr = pd.DataFrame()

    return df_dre, df_paulo, df_clau, df_sdr

df_dre, df_paulo, df_clau, df_sdr = load_data()

# --- Filtros da Barra Lateral ---
st.sidebar.image("https://img.icons8.com/color/96/000000/sun--v1.png", width=60) # Ícone de sol placeholder
st.sidebar.header("🔍 Filtros de Análise")

# Filtro de Mês (Focando em Dezembro/2025 e Janeiro/2026 conforme solicitado)
meses_opcoes = {'Dezembro 2025': (2025, 12), 'Janeiro 2026': (2026, 1), 'Ambos': 'Ambos'}
mes_selecionado = st.sidebar.selectbox("Selecione o Período", list(meses_opcoes.keys()))

# --- Lógica de Filtragem por Data ---
def filtrar_por_mes(df, coluna_data, filtro_mes):
    if filtro_mes == 'Ambos':
        return df[(df[coluna_data].dt.year.isin([2025, 2026])) & (df[coluna_data].dt.month.isin([12, 1]))]
    else:
        ano, mes = meses_opcoes[filtro_mes]
        return df[(df[coluna_data].dt.year == ano) & (df[coluna_data].dt.month == mes)]

df_dre_filtrado = filtrar_por_mes(df_dre, 'Data', mes_selecionado) if not df_dre.empty else df_dre
df_paulo_filtrado = filtrar_por_mes(df_paulo, 'Data da criação', mes_selecionado) if not df_paulo.empty else df_paulo
df_clau_filtrado = filtrar_por_mes(df_clau, 'Data da criação', mes_selecionado) if not df_clau.empty else df_clau

# --- Lógica de Funil Cumulativo ---
def calcular_funil(nome_vendedor, df_propostas, df_vendas):
    # Quantidade de vendas (última etapa)
    vendas = df_vendas[df_vendas['Responsável'].str.contains(nome_vendedor, na=False, case=False)].shape[0]
    
    # Contagem de status atual na planilha de propostas em aberto
    status_counts = df_propostas['Estágio do Processo'].value_counts()
    
    # Mapeando os status (ajuste os nomes exatos caso a planilha mude)
    qtd_negociacao_atual = status_counts.filter(like='Negociação').sum()
    qtd_proposta_atual = status_counts.filter(like='Proposta').sum()
    qtd_agendados_atual = status_counts.filter(like='Agendados').sum()
    
    # Lógica Cumulativa: Se passou, conta nos anteriores
    total_vendas = vendas
    total_negociacao = qtd_negociacao_atual + total_vendas
    total_proposta = qtd_proposta_atual + total_negociacao
    total_agendados = qtd_agendados_atual + total_proposta
    
    return pd.DataFrame({
        'Etapa': ['Agendados', 'Proposta', 'Negociação', 'Venda'],
        'Quantidade': [total_agendados, total_proposta, total_negociacao, total_vendas]
    })

# Calculando para Paulo e Claudenia
funil_paulo = calcular_funil('Paulo Silva', df_paulo_filtrado, df_dre_filtrado)
funil_clau = calcular_funil('Claudenia Castro', df_clau_filtrado, df_dre_filtrado)

# --- Conteúdo Principal do Dashboard ---
st.title("☀️ Dashboard Comercial Mais Sol")
st.markdown("Análise de conversão do time de Vendas e SDR.")

st.markdown("---")

# --- Seção 1: SDR ---
st.subheader("🎯 Conversão SDR (Leads -> Agendamentos)")
st.info("Nota: A visualização exata da conversão Diária/Semanal/Mensal do SDR requer que a 'linha 6' e as datas do CSV 'KPI Marketing - 2026 - SDR.csv' sejam transpostas para um formato de colunas limpo.")
# Aqui você pode adicionar gráficos de linha com px.line lendo os dados tratados do df_sdr
# Exemplo genérico:
# st.plotly_chart(px.line(df_sdr_tratado, x='Data', y='Conversão', color='Período'))

# --- Seção 2: Eficiência dos Vendedores ---
st.header("📊 Eficiência de Vendas no Funil")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Funil: Paulo Silva")
    fig_funil_paulo = px.funnel(
        funil_paulo, 
        x='Quantidade', 
        y='Etapa',
        color_discrete_sequence=['#F39C12'] # Laranja remetendo ao Sol
    )
    st.plotly_chart(fig_funil_paulo, use_container_width=True)
    
    # Calcular e mostrar conversão de agendado para venda
    conv_paulo = (funil_paulo.iloc[3]['Quantidade'] / funil_paulo.iloc[0]['Quantidade'] * 100) if funil_paulo.iloc[0]['Quantidade'] > 0 else 0
    st.metric(label="Taxa de Conversão Final (Agendado -> Venda)", value=f"{conv_paulo:.1f}%")

with col2:
    st.subheader("Funil: Claudenia Castro")
    fig_funil_clau = px.funnel(
        funil_clau, 
        x='Quantidade', 
        y='Etapa',
        color_discrete_sequence=['#E67E22']
    )
    st.plotly_chart(fig_funil_clau, use_container_width=True)
    
    # Calcular e mostrar conversão de agendado para venda
    conv_clau = (funil_clau.iloc[3]['Quantidade'] / funil_clau.iloc[0]['Quantidade'] * 100) if funil_clau.iloc[0]['Quantidade'] > 0 else 0
    st.metric(label="Taxa de Conversão Final (Agendado -> Venda)", value=f"{conv_clau:.1f}%")

st.markdown("---")

# --- Dados Tabelados ---
st.subheader("Tabelas de Vendas Fechadas (DRE)")
st.dataframe(df_dre_filtrado[['Nome do Cliente', 'Origem do Processo', 'Data', 'Responsável', 'Valor do Proposta origem']])