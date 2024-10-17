import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

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

# Gráfico de combinação com a receita diluída do mês corrente
fig, ax = plt.subplots(figsize=(8, 4))  # Tamanho ajustado

# Barras da receita
ax.bar(df['Mês'], df['Receita Vendas Integrais (R$)'], color='blue', label='Receita Vendas Integrais', width=0.4)
ax.bar(df['Mês'], df['Receita Vendas Diluídas Corrente (R$)'], bottom=df['Receita Vendas Integrais (R$)'], color='lightblue', label='Receita Diluída do Mês Corrente', width=0.4)
ax.bar(df['Mês'], df['Receita Vendas Diluídas Meses Anteriores (R$)'], bottom=df['Receita Vendas Integrais (R$)'] + df['Receita Vendas Diluídas Corrente (R$)'], color='gray', label='Receita Diluída de Meses Anteriores', width=0.4)

# Linha da receita total
ax.plot(df['Mês'], df['Receita Total (R$)'], color='green', marker='o', label='Receita Total')

# Formatação do eixo Y para valores financeiros
formatter = FuncFormatter(lambda x, _: f'R$ {x:,.0f}'.replace(",", "X").replace(".", ",").replace("X", "."))
ax.yaxis.set_major_formatter(formatter)

# Rótulos e legenda
ax.set_xlabel("Meses")
ax.set_ylabel("Receita (R$)")
ax.set_title("Projeção de Receita Mensal")

# Mover a legenda para fora do gráfico
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))  # Posiciona à direita

# Ajustar layout do gráfico para se adequar ao espaço da legenda
plt.tight_layout()

st.pyplot(fig)
