import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Função para formatar valores monetários
def moeda_format(val):
    return f'R$ {val:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")

# Configurações iniciais da página
st.set_page_config(page_title="Simulador de Receita", layout="wide")

st.title("Simulador de Receita - Múltiplos Períodos de Prestação de Serviço")
st.markdown(
    """
    Simulador de receita por tipo de reconhecimento.
    """
)

# Entradas do usuário: data_editor
st.markdown("### Insira os valores de GMV conforme regra de reconhecimento de receita")
meses = [f'Mês {i+1}' for i in range(24)]  # Mudança para 24 meses
df = pd.DataFrame({
    'Mês': meses,
    'Integral': [0.0] * 24,
    'Conf. Prest. (6m)': [0.0] * 24,
    'Conf. Prest. (8m)': [0.0] * 24,
    'Conf. Prest. (10m)': [0.0] * 24,
    'Conf. Prest. (12m)': [0.0] * 24,
    'Conf. Prest. (14m)': [0.0] * 24,
    'Conf. Prest. (16m)': [0.0] * 24,
    'Conf. Prest. (18m)': [0.0] * 24,
    'Conf. Prest. (20m)': [0.0] * 24,
    'Conf. Prest. (22m)': [0.0] * 24,
    'Conf. Prest. (24m)': [0.0] * 24,
})

# Input para edição de dados
st.markdown("#### Tabela de GMV (input usuário)")
df = st.data_editor(df, key="input_data2", hide_index=True)

# Cálculos de receitas diluídas de acordo com os períodos
df['Receita Vendas Integrais'] = df['Integral']

# Inicializando colunas de receita diluída
for col in df.columns[2:]:
    if 'Conf. Prest.' in col:  # Verificar se a coluna se refere a valores diluídos
        meses_diluicao = int(col.split('(')[1].replace('m)', ''))  # Extrai o número de meses da coluna
        df[f'Receita {meses_diluicao} meses'] = 0.0
        for i in range(0, len(df) - meses_diluicao + 1):
            # Garantir que o tamanho das fatias seja compatível
            df.loc[i:i+meses_diluicao-1, f'Receita {meses_diluicao} meses'] += df.loc[i, col] / meses_diluicao

# Remover colunas de valores antes de exibir
colunas_a_remover = [col for col in df.columns if 'Integral' in col or 'Conf. Prest.' in col]
df_receita = df.drop(columns=colunas_a_remover)

# Cálculo de receita total
df_receita['Receita Total'] = df_receita[[f'Receita {meses_diluicao} meses' for meses_diluicao in range(6, 25, 2)]].sum(axis=1)

# Formatação dos valores
df_receita_formatado = df_receita.copy()
df_receita_formatado['Receita Total'] = df_receita_formatado['Receita Total'].apply(moeda_format)

# **GRÁFICO 1** - Gráfico de colunas empilhadas e linha com popup customizado e volume de vendas calculado
st.markdown("### Gráfico de Receita por Tipo de Reconhecimento")

# Gráfico de combinação (colunas empilhadas e linha)
fig_comb = go.Figure()

# Definir uma paleta de cores visualmente diferenciáveis
cores = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']

# Calcular o volume de vendas como o somatório dos valores de cada linha da tabela inserida pelo usuário
volume_vendas = df[['Integral'] + [f'Conf. Prest. ({meses}m)' for meses in range(6, 25, 2)]].sum(axis=1)

# Função para gerar hovertemplate customizado
def gerar_hovertemplate(valores, volumes):
    return [f'R$ {valor:.2f}<br>Volume de Vendas: R$ {volume:.2f}' if valor > 0 else ' ' 
            for valor, volume in zip(valores, volumes)]

def gerar_hovertemplate_simplificado(valores):
    return ['R$ %{y:.2f}' if valor > 0 else ' ' for valor in valores]

# Adicionando as barras empilhadas para cada tipo de receita com hovertemplate customizado
fig_comb.add_trace(go.Bar(
    x=df['Mês'],
    y=df_receita['Receita Vendas Integrais'],
    name='Receita - Integrais',
    marker_color='blue',  # Cor fixa para vendas integrais
    customdata=volume_vendas,  # Adicionar os dados de volume ao customdata
    hovertemplate=gerar_hovertemplate_simplificado(df_receita['Receita Vendas Integrais'])  # Ocultar valores zero
))

for i, meses in enumerate(range(6, 25, 2)):
    fig_comb.add_trace(go.Bar(
        x=df['Mês'],
        y=df_receita[f'Receita {meses} meses'],
        name=f'Receita - Conf. Prestação ({meses}m)',
        marker_color=cores[i],  # Usar cores diferenciáveis da lista
        customdata=volume_vendas,  # Adicionar volume de vendas ao hovertemplate
        hovertemplate=gerar_hovertemplate_simplificado(df_receita[f'Receita {meses} meses'])  # Ocultar valores zero
    ))

# Adicionando a linha para o volume total de receitas no mês
volume_total_receita = df_receita[['Receita Vendas Integrais'] + [f'Receita {meses} meses' for meses in range(6, 25, 2)]].sum(axis=1)
fig_comb.add_trace(go.Scatter(
    x=df['Mês'],
    y=volume_total_receita,
    mode='lines+markers',
    name='Receita - Total',
    line=dict(color='black', width=2),
    marker=dict(size=8),
    customdata=volume_vendas,  # Incluir volume de vendas também na linha
    hovertemplate='R$ %{y:.2f}<br>Volume de Vendas: R$ %{customdata:.2f}'  # Exibir valor total e volume de vendas
))

# Customizar o layout do gráfico
fig_comb.update_layout(
    xaxis_title="Meses",
    yaxis_title="Receita (R$)",
    barmode='stack',  # Modo de colunas empilhadas
    hovermode="x unified",  # Unificar o hover em todos os traços ao passar o mouse
    margin=dict(l=0, r=0, t=50, b=0)
)

# Exibir o gráfico de combinação
st.plotly_chart(fig_comb, use_container_width=True)

### TABELA TOTAL DE VENDAS, RECEITA E PERCENTUAIS
# Cálculo do total de vendas por mês (somando todas as vendas integrais e prestação)
df_vendas_total_mensal = df[['Integral'] + [f'Conf. Prest. ({meses}m)' for meses in range(6, 25, 2)]].sum(axis=1)

# Criar um dataframe para exibir as vendas totais
df_vendas_total_mensal_df = pd.DataFrame(df_vendas_total_mensal).T
df_vendas_total_mensal_df.columns = df['Mês']  # Usar os nomes dos meses como cabeçalhos de coluna
df_vendas_total_mensal_df.index = ['Total de Vendas']

# Cálculo da soma total por mês, considerando todas as receitas (integral + diluídas)
df_receita['Receita Total'] = df_receita[['Receita Vendas Integrais'] + 
                                         [f'Receita {meses} meses' for meses in range(6, 25, 2)]].sum(axis=1)

# Criar um dataframe para exibir a receita total
df_receita_total_mensal_df = pd.DataFrame(df_receita['Receita Total']).T
df_receita_total_mensal_df.columns = df['Mês']  # Usar os nomes dos meses como cabeçalhos de coluna
df_receita_total_mensal_df.index = ['Total de Receita']

# Cálculo do valor da receita de Novas Vendas (vendas integrais + 1ª parcela de diluídas)
df_novas_vendas = df_receita['Receita Vendas Integrais'].copy()
for meses in range(6, 25, 2):
    df_novas_vendas += df[f'Conf. Prest. ({meses}m)'] / meses

# Criar dataframe para as novas vendas
df_novas_vendas_df = pd.DataFrame(df_novas_vendas).T
df_novas_vendas_df.columns = df['Mês']
df_novas_vendas_df.index = ['Receita Novas Vendas']

# Cálculo do valor da receita de Vendas Legado (parcelas de vendas anteriores)
df_vendas_legado = df_receita['Receita Total'] - df_novas_vendas
df_vendas_legado_df = pd.DataFrame(df_vendas_legado).T
df_vendas_legado_df.columns = df['Mês']
df_vendas_legado_df.index = ['Receita Vendas Legado']

# Cálculo do % de Novas Vendas
df_novas_vendas_percent = (df_novas_vendas / df_receita['Receita Total']) * 100
df_novas_vendas_percent_df = pd.DataFrame(df_novas_vendas_percent).T
df_novas_vendas_percent_df.columns = df['Mês']
df_novas_vendas_percent_df.index = ['% Novas Vendas']

# Cálculo do % de Vendas Legado
df_vendas_legado_percent = (df_vendas_legado / df_receita['Receita Total']) * 100
df_vendas_legado_percent_df = pd.DataFrame(df_vendas_legado_percent).T
df_vendas_legado_percent_df.columns = df['Mês']
df_vendas_legado_percent_df.index = ['% Vendas Legado']

# Concatenar as linhas (Total de Vendas, Total de Receita, Receita Novas Vendas, Receita Vendas Legado, % Novas Vendas, % Vendas Legado)
df_totais_mensal = pd.concat([df_vendas_total_mensal_df, 
                              df_receita_total_mensal_df, 
                              df_novas_vendas_percent_df, 
                              df_novas_vendas_df,  
                              df_vendas_legado_percent_df,                              
                              df_vendas_legado_df])

# Formatar os valores monetários e percentuais
df_totais_mensal_formatado = df_totais_mensal.copy()
df_totais_mensal_formatado.loc['Total de Vendas'] = df_totais_mensal_formatado.loc['Total de Vendas'].apply(moeda_format)
df_totais_mensal_formatado.loc['Total de Receita'] = df_totais_mensal_formatado.loc['Total de Receita'].apply(moeda_format)
df_totais_mensal_formatado.loc['Receita Novas Vendas'] = df_totais_mensal_formatado.loc['Receita Novas Vendas'].apply(moeda_format)
df_totais_mensal_formatado.loc['% Novas Vendas'] = df_totais_mensal_formatado.loc['% Novas Vendas'].apply(lambda x: f'{x:.2f}%')
df_totais_mensal_formatado.loc['Receita Vendas Legado'] = df_totais_mensal_formatado.loc['Receita Vendas Legado'].apply(moeda_format)
df_totais_mensal_formatado.loc['% Vendas Legado'] = df_totais_mensal_formatado.loc['% Vendas Legado'].apply(lambda x: f'{x:.2f}%')

# Exibir a nova tabela com o total de vendas, total de receita, receita de novas vendas, receita de vendas legado, % novas vendas e % vendas legado
st.markdown("#### Total de Vendas, Receita e Percentuais por Mês")
st.dataframe(df_totais_mensal_formatado)




# Transpor a tabela para colocar os meses como colunas e os tipos de reconhecimento como linhas
df_receita_transposta = df_receita.set_index('Mês').T

# Formatação dos valores monetários após a transposição, sem a linha de total
df_receita_transposta_formatado = df_receita_transposta.applymap(moeda_format)

# Exibir a tabela transposta formatada
st.markdown("#### Receita por Tipo de Reconhecimento")
st.dataframe(df_receita_transposta_formatado)
