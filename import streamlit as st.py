import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import subprocess
import sys

# --- TRUQUE: Forçar a instalação do openpyxl ---
try:
    import openpyxl
except ImportError:
    st.warning("Instalando o openpyxl... Aguarde um instante.")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl
    st.success("Instalação concluída! Recarregando...")
    st.rerun()

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
        df_dre = pd.read_csv("DRE_Dezembro Origem Sun Janeiro e Fervereiro.csv")
        df_dre['Data'] = pd.to_datetime(df_dre['Data'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar DRE: {e}")
        df_dre = pd.DataFrame()

    # 2. Carregar Propostas em Aberto (Paulo e Claudenia)
    try:
        df_paulo = pd.read_csv("Propostas em aberto sun Paulo.csv")
        df_paulo['Data da criação'] = pd.to_datetime(df_paulo['Data da criação'], errors='coerce')
        
        df_clau = pd.read_csv("Propostas em aberto sun CLau.csv")
        df_clau['Data da criação'] = pd.to_datetime(df_clau['Data da criação'], errors='coerce')
    except Exception as e:
        st.error(f"Erro ao carregar Propostas: {e}")
        df_paulo, df_clau = pd.DataFrame(), pd.DataFrame()

    # 3. Carregar SDR (Aba específica do ficheiro Excel)
    try:
        # Ajuste o nome da aba ('SDR') ou a linha a saltar (skiprows) conforme a estrutura real do seu Excel
        df_sdr = pd.read_csv("KPI Marketing - 2026.csv", sheet_name="SDR", skiprows=2) 
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
        qtd_agendados_atual = status_counts.filter(like='Agendados').sum()
    
    # Lógica Cumulativa
    total_vendas = vendas
    total_negociacao = qtd_negociacao_atual + total_vendas
    total_proposta = qtd_proposta_atual + total_negociacao
    total_agendados = qtd_agendados_atual + total_proposta
    
    return pd.DataFrame({
        'Etapa': ['Agendados', 'Proposta', 'Negociação', 'Venda'],
        'Quantidade': [total_agendados, total_proposta, total_negociacao, total_vendas]
    })

funil_paulo = calcular_funil('Paulo Silva', df_paulo_filtrado, df_dre_filtrado)
funil_clau = calcular_funil('Claudenia Castro', df_clau_filtrado, df_dre_filtrado)

# --- Conteúdo Principal do Dashboard ---
st.title("☀️ Dashboard Comercial Mais Sol")
st.markdown("Análise de conversão da equipa de Vendas e SDR.")

st.markdown("---")

# --- Seção 1: SDR ---
st.subheader("🎯 Conversão SDR (Leads -> Agendamentos)")
st.info("Nota: Para a visualização da conversão Diária/Semanal/Mensal do SDR, os dados do Excel precisam de ser transformados (melt) para estruturar as datas em colunas adequadas para o gráfico.")

# --- Seção 2: Eficiência dos Vendedores ---
st.header("📊 Eficiência de Vendas no Funil")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Funil: Paulo Silva")
    fig_funil_paulo = px.funnel(
        funil_paulo, 
        x='Quantidade', 
        y='Etapa',
        color_discrete_sequence=['#F39C12']
    )
    st.plotly_chart(fig_funil_paulo, use_container_width=True)
    
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
    
    conv_clau = (funil_clau.iloc[3]['Quantidade'] / funil_clau.iloc[0]['Quantidade'] * 100) if funil_clau.iloc[0]['Quantidade'] > 0 else 0
    st.metric(label="Taxa de Conversão Final (Agendado -> Venda)", value=f"{conv_clau:.1f}%")

st.markdown("---")

# --- Dados Tabelados ---
st.subheader("Tabelas de Vendas Fechadas (DRE)")
if not df_dre_filtrado.empty:
    st.dataframe(df_dre_filtrado[['Nome do Cliente', 'Origem do Processo', 'Data', 'Responsável', 'Valor do Proposta origem']])
else:
    st.warning("Não há dados de vendas para o período selecionado.")


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

# --- Funções de Carregamento de Dados (AGORA EM CSV) ---
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

    # 3. Carregar SDR (Pulando as duas primeiras linhas de cabeçalho bagunçado)
    try:
        df_sdr = pd.read_csv("KPI Marketing - 2026.xlsx - SDR.csv", skiprows=2) 
    except Exception as e:
        st.error(f"Erro ao carregar SDR: {e}")
        df_sdr = pd.DataFrame()

    return df_dre, df_paulo, df_clau, df_sdr

df_dre, df_paulo, df_clau, df_sdr = load_data()

# --- Filtros da Barra Lateral ---
st.sidebar.image("https://img.icons8.com/color/96/000000/sun--v1.png", width=60) # Ícone de sol
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
        qtd_agendados_atual = status_counts.filter(like='Agendados').sum()
    
    # Lógica Cumulativa (Quem comprou, passou por tudo. Quem negociou, passou por proposta...)
    total_vendas = vendas
    total_negociacao = qtd_negociacao_atual + total_vendas
    total_proposta = qtd_proposta_atual + total_negociacao
    total_agendados = qtd_agendados_atual + total_proposta
    
    return pd.DataFrame({
        'Etapa': ['Agendados', 'Proposta', 'Negociação', 'Venda'],
        'Quantidade': [total_agendados, total_proposta, total_negociacao, total_vendas]
    })

funil_paulo = calcular_funil('Paulo Silva', df_paulo_filtrado, df_dre_filtrado)
funil_clau = calcular_funil('Claudenia Castro', df_clau_filtrado, df_dre_filtrado)

# --- Conteúdo Principal do Dashboard ---
st.title("☀️ Dashboard Comercial Mais Sol")
st.markdown("Análise de conversão da equipe de Vendas e SDR.")

st.markdown("---")

# --- Seção 1: SDR ---
st.subheader("🎯 Conversão SDR (Leads -> Agendamentos)")
st.info("Assim que confirmarmos que o funil de vendas carregou corretamente com os arquivos CSV, adicionaremos os gráficos de conversão diária, semanal e mensal do SDR aqui!")

# --- Seção 2: Eficiência dos Vendedores ---
st.header("📊 Eficiência de Vendas no Funil")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Funil: Paulo Silva")
    fig_funil_paulo = px.funnel(
        funil_paulo, 
        x='Quantidade', 
        y='Etapa',
        color_discrete_sequence=['#F39C12']
    )
    st.plotly_chart(fig_funil_paulo, use_container_width=True)
    
    conv_paulo = (funil_paulo.iloc[3]['Quantidade'] / funil_paulo.iloc[0]['Quantidade'] * 100) if funil_paulo.iloc[0]['Quantidade'] > 0 else 0
    st.metric(label="Taxa de Conversão (Agendado -> Venda)", value=f"{conv_paulo:.1f}%")

with col2:
    st.subheader("Funil: Claudenia Castro")
    fig_funil_clau = px.funnel(
        funil_clau, 
        x='Quantidade', 
        y='Etapa',
        color_discrete_sequence=['#E67E22']
    )
    st.plotly_chart(fig_funil_clau, use_container_width=True)
    
    conv_clau = (funil_clau.iloc[3]['Quantidade'] / funil_clau.iloc[0]['Quantidade'] * 100) if funil_clau.iloc[0]['Quantidade'] > 0 else 0
    st.metric(label="Taxa de Conversão (Agendado -> Venda)", value=f"{conv_clau:.1f}%")

st.markdown("---")

# --- Dados Tabelados ---
st.subheader("Tabelas de Vendas Fechadas (DRE)")
if not df_dre_filtrado.empty:
    st.dataframe(df_dre_filtrado[['Nome do Cliente', 'Origem do Processo', 'Data', 'Responsável', 'Valor do Proposta origem']])
else:
    st.warning("Não há dados de vendas para o período selecionado.")

