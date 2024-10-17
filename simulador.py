import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Função para formatar valores monetários
def moeda_format(val):
    return f'R$ {val:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")

# Configurações iniciais da página
st.set_page_config(page_title="Simulador de Receita", layout="wide")

# Título e descrição
st.title("Simulador de Receita")
st.markdown(
    """
    Ferramenta utilizada para simular a projeção de receita ao longo de 12 meses de acordo com o GMV e a composição do mix de vendas.
    """
)

# Entradas do usuário: data_editor
st.markdown("### Insira os dados de GMV e percentual de vendas integrais (em %)")
meses = [f'Mês {i+1}' for i in range(12)]
df = pd.DataFrame({
    'Mês': meses,
    'GMV (R$)': [0.0] * 12,
    '% Integral': [0.0] * 12,  # Percentual de 0 a 100
})

# Colunas para exibir lado a lado
col1, col2 = st.columns([0.6, 2.4])

with col1:
    # Input para a edição de dados
    st.markdown("#### Edição de Dados")
    df = st.data_editor(df, key="input_data", hide_index=True)

with col2:
    # Converte os percentuais de 0 a 100 para 0 a 1
    df['% Integral'] = df['% Integral'] / 100
    df['% Diluído'] = 1 - df['% Integral']

    # Cálculos de receita
    df['Receita Vendas Integrais (R$)'] = df['GMV (R$)'] * df['% Integral']
    df['Receita Vendas Diluídas Corrente (R$)'] = (df['GMV (R$)'] * df['% Diluído']) / 12

    # Receita gerada por vendas diluídas de meses anteriores
    df['Receita Vendas Diluídas Meses Anteriores (R$)'] = 0.0

    for i in range(1, 12):
        df.loc[i:, 'Receita Vendas Diluídas Meses Anteriores (R$)'] += df.loc[i-1, 'Receita Vendas Diluídas Corrente (R$)']

    # Cálculo de receita total
    df['Receita Total (R$)'] = df['Receita Vendas Integrais (R$)'] + df['Receita Vendas Diluídas Corrente (R$)'] + df['Receita Vendas Diluídas Meses Anteriores (R$)']

    # Formatação dos valores
    df_formatado = df.copy()
    df_formatado['GMV (R$)'] = df_formatado['GMV (R$)'].apply(moeda_format)
    df_formatado['Receita Vendas Integrais (R$)'] = df_formatado['Receita Vendas Integrais (R$)'].apply(moeda_format)
    df_formatado['Receita Vendas Diluídas Corrente (R$)'] = df_formatado['Receita Vendas Diluídas Corrente (R$)'].apply(moeda_format)
    df_formatado['Receita Vendas Diluídas Meses Anteriores (R$)'] = df_formatado['Receita Vendas Diluídas Meses Anteriores (R$)'].apply(moeda_format)
    df_formatado['Receita Total (R$)'] = df_formatado['Receita Total (R$)'].apply(moeda_format)

    # Exibir a tabela formatada
    st.markdown("#### Tabela de Receitas")
    st.dataframe(df_formatado, hide_index=True)

# Gráfico interativo usando Plotly
fig = go.Figure()

# Adicionando as barras de Receita Vendas Integrais
fig.add_trace(go.Bar(
    x=df['Mês'], 
    y=df['Receita Vendas Integrais (R$)'], 
    name='Receita Vendas Integrais',
    marker_color='blue'
))

# Adicionando as barras de Receita Vendas Diluídas Corrente
fig.add_trace(go.Bar(
    x=df['Mês'], 
    y=df['Receita Vendas Diluídas Corrente (R$)'], 
    name='Receita Diluída do Mês Corrente',
    marker_color='lightblue'
))

# Adicionando as barras de Receita Vendas Diluídas Meses Anteriores
fig.add_trace(go.Bar(
    x=df['Mês'], 
    y=df['Receita Vendas Diluídas Meses Anteriores (R$)'], 
    name='Receita Diluída de Meses Anteriores',
    marker_color='gray'
))

# Adicionando a linha da Receita Total
fig.add_trace(go.Scatter(
    x=df['Mês'], 
    y=df['Receita Total (R$)'], 
    mode='lines+markers',
    name='Receita Total',
    line=dict(color='green')
))

# Customizando o layout do gráfico
fig.update_layout(
    title="Projeção de Receita Mensal",
    xaxis_title="Meses",
    yaxis_title="Receita (R$)",
    barmode='stack',
    hovermode="x",
    legend=dict(x=1.05, y=1),
    margin=dict(l=0, r=0, t=50, b=0)
)

# Exibindo o gráfico no Streamlit
st.plotly_chart(fig, use_container_width=True)
