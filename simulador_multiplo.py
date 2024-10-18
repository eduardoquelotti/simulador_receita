import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing  # Para a previsão

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

# Geração dinâmica dos meses e colunas
num_months = 24
meses = [f'Mês {i+1}' for i in range(num_months)]
conf_prest_meses = range(6, 25, 2)  # De 6 até 24 meses, com passo de 2
conf_prest_cols = [f'Conf. Prest. ({m}m)' for m in conf_prest_meses]

# Inicializar ou recuperar o DataFrame de GMV do estado da sessão
if 'df_gmv' not in st.session_state:
    # DataFrame inicial com zeros
    df = pd.DataFrame({
        'Mês': meses,
        'Integral': [0.0] * num_months
    })
    for col in conf_prest_cols:
        df[col] = [0.0] * num_months
    st.session_state.df_gmv = df.copy()
else:
    df = st.session_state.df_gmv.copy()

# Botão para preencher a tabela com valores aleatórios
if st.button("Preencher GMV com Valores Aleatórios"):
    # Gerar valores aleatórios para cada coluna relevante
    for col in ['Integral'] + conf_prest_cols:
        df[col] = np.random.uniform(100000, 1000000, size=num_months)
    st.session_state.df_gmv = df.copy()

st.markdown("#### Tabela de GMV")
df = st.data_editor(df, key="input_data2", hide_index=True)
st.session_state.df_gmv = df.copy()

# Cálculos de receitas diluídas de acordo com os períodos
df_receita = pd.DataFrame({'Mês': df['Mês']})
df_receita['Receita - Integral'] = df['Integral']

for meses_diluicao in conf_prest_meses:
    col_name = f'Conf. Prest. ({meses_diluicao}m)'
    receita_col = f'Receita - Conf. Prest. ({meses_diluicao}m)'
    receita_diluida = np.zeros(len(df))
    for idx in range(len(df)):
        valor = df.at[idx, col_name]
        meses_restantes = len(df) - idx
        meses_aplicaveis = min(meses_diluicao, meses_restantes)
        if valor != 0:
            receita_diluida[idx:idx+meses_aplicaveis] += valor / meses_diluicao
    df_receita[receita_col] = receita_diluida

# Cálculo de receita total
revenue_cols = ['Receita - Integral'] + [f'Receita - Conf. Prest. ({m}m)' for m in conf_prest_meses]
df_receita['Receita Total'] = df_receita[revenue_cols].sum(axis=1)

# Cálculo da Receita Total Acumulada
df_receita['Receita Total Acumulada'] = df_receita['Receita Total'].cumsum()

# Calcular o volume de vendas como o somatório dos valores de cada linha da tabela inserida pelo usuário
df['Total Vendas'] = df[['Integral'] + conf_prest_cols].sum(axis=1)
volume_vendas = df['Total Vendas']

# Calcular as Vendas Acumuladas
df_receita['Vendas Acumuladas'] = df['Total Vendas'].cumsum()

# **GRÁFICO 1 e GRÁFICO 2** - Alternar entre gráficos com o mesmo título
st.markdown("### Receita Total e por Tipo de Reconhecimento")

# Criar um botão de rádio para selecionar o gráfico
opcao_grafico = st.radio(
    "Selecione o tipo de gráfico:",
    ('Gráfico de Barras Empilhadas', 'Gráfico de Linhas')
)

if opcao_grafico == 'Gráfico de Barras Empilhadas':
    # **GRÁFICO 1** - Gráfico de Receita por Tipo de Reconhecimento
    # Gráfico de combinação (colunas empilhadas e linha)
    fig_comb = go.Figure()

    # Definir uma paleta de cores visualmente diferenciáveis
    cores = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']

    # Adicionando as barras empilhadas para cada tipo de receita com hovertemplate customizado
    fig_comb.add_trace(go.Bar(
        x=df_receita['Mês'],
        y=df_receita['Receita - Integral'],
        name='Receita - Integral',
        marker_color='blue',
        customdata=volume_vendas,
        hovertemplate='Receita: R$ %{y:.2f}'  # Hovertemplate simplificado
    ))

    for i, m in enumerate(conf_prest_meses):
        receita_col = f'Receita - Conf. Prest. ({m}m)'
        fig_comb.add_trace(go.Bar(
            x=df_receita['Mês'],
            y=df_receita[receita_col],
            name=f'Receita - Conf. Prestação ({m}m)',
            marker_color=cores[i % len(cores)],
            customdata=volume_vendas,
            hovertemplate='Receita: R$ %{y:.2f}'  # Hovertemplate simplificado
        ))

    # Adicionando a linha para o volume total de receitas no mês
    fig_comb.add_trace(go.Scatter(
        x=df_receita['Mês'],
        y=df_receita['Receita Total'],
        mode='lines+markers',
        name='Receita - Total',
        line=dict(color='black', width=2),
        marker=dict(size=8),
        customdata=volume_vendas,
        hovertemplate='Receita Total: R$ %{y:.2f}<br>Volume de Vendas: R$ %{customdata:.2f}'
    ))

    # Customizar o layout do gráfico
    fig_comb.update_layout(
        xaxis_title="Meses",
        yaxis_title="Receita (R$)",
        barmode='stack',
        hovermode="x unified",
        margin=dict(l=0, r=0, t=50, b=0)
    )

    # Exibir o gráfico de combinação
    st.plotly_chart(fig_comb, use_container_width=True)

elif opcao_grafico == 'Gráfico de Linhas':
    # **GRÁFICO 2** - Gráfico de linhas mostrando a receita ao longo do tempo por tipo de reconhecimento
    # Criar o gráfico de linhas
    fig_lines = go.Figure()

    # Definir a mesma paleta de cores para consistência
    cores = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']

    # Adicionar a linha para 'Receita - Integral'
    fig_lines.add_trace(go.Scatter(
        x=df_receita['Mês'],
        y=df_receita['Receita - Integral'],
        mode='lines+markers',
        name='Receita - Integral',
        line=dict(color='blue', width=2),
        marker=dict(size=6),
        hovertemplate='Receita Integral: R$ %{y:.2f}'
    ))

    # Adicionar linhas para cada tipo de 'Receita - Conf. Prest.'
    for i, m in enumerate(conf_prest_meses):
        receita_col = f'Receita - Conf. Prest. ({m}m)'
        fig_lines.add_trace(go.Scatter(
            x=df_receita['Mês'],
            y=df_receita[receita_col],
            mode='lines+markers',
            name=f'Receita - Conf. Prest. ({m}m)',
            line=dict(color=cores[i % len(cores)], width=2),
            marker=dict(size=6),
            hovertemplate=f'Receita Conf. Prest. ({m}m): R$ '+'%{y:.2f}'
        ))

    # Adicionar a linha para 'Receita Total'
    fig_lines.add_trace(go.Scatter(
        x=df_receita['Mês'],
        y=df_receita['Receita Total'],
        mode='lines+markers',
        name='Receita Total',
        line=dict(color='black', width=3, dash='dash'),
        marker=dict(size=8),
        hovertemplate='Receita Total: R$ %{y:.2f}'
    ))

    # Configurar o layout do gráfico
    fig_lines.update_layout(
        xaxis_title="Meses",
        yaxis_title="Receita (R$)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=50, b=0),
        legend_title_text='Tipo de Reconhecimento'
    )

    # Exibir o gráfico de linhas
    st.plotly_chart(fig_lines, use_container_width=True)

# **GRÁFICO 3** - Gráfico de Receita Total Acumulada
st.markdown("### Receita Total Acumulada ao Longo do Tempo")

fig_cumulative = go.Figure()

fig_cumulative.add_trace(go.Scatter(
    x=df_receita['Mês'],
    y=df_receita['Receita Total Acumulada'],
    mode='lines+markers',
    name='Receita Total Acumulada',
    line=dict(color='green', width=3),
    marker=dict(size=8),
    hovertemplate='Receita Acumulada: R$ %{y:.2f}'
))

# **Nova Linha**: Vendas Acumuladas
fig_cumulative.add_trace(go.Scatter(
    x=df_receita['Mês'],
    y=df_receita['Vendas Acumuladas'],
    mode='lines+markers',
    name='Vendas Acumuladas',
    line=dict(color='purple', width=3, dash='dash'),
    marker=dict(size=8),
    hovertemplate='Vendas Acumuladas: R$ %{y:.2f}'
))

# Configurar o layout do gráfico
fig_cumulative.update_layout(
    xaxis_title="Meses",
    yaxis_title="Receita Acumulada (R$)",
    hovermode="x unified",
    margin=dict(l=0, r=0, t=50, b=0),
    legend_title_text='Métricas'
)

# Exibir o gráfico de receita acumulada
st.plotly_chart(fig_cumulative, use_container_width=True)

# **PREVISÃO** - Previsão de Receita Futura
st.markdown("### Previsão de Receita Futura")

# Preparar os dados de treinamento
train_data = df_receita['Receita Total']

# Definir o modelo de suavização exponencial
model = ExponentialSmoothing(train_data, trend='additive', seasonal=None)

# Ajustar o modelo
model_fit = model.fit()

# Fazer previsões para os próximos 6 meses
forecast_periods = 6
forecast = model_fit.forecast(forecast_periods)

# Criar um DataFrame para as previsões
future_months = [f'Mês {num_months + i + 1}' for i in range(forecast_periods)]
df_forecast = pd.DataFrame({
    'Mês': future_months,
    'Receita Prevista': forecast
})

# Combinar dados reais e previstos
df_combined = pd.concat([df_receita[['Mês', 'Receita Total']], df_forecast], ignore_index=True)

# Criar o gráfico de previsão
fig_forecast = go.Figure()

fig_forecast.add_trace(go.Scatter(
    x=df_receita['Mês'],
    y=df_receita['Receita Total'],
    mode='lines+markers',
    name='Receita Real',
    line=dict(color='blue', width=2),
    marker=dict(size=6),
    hovertemplate='Receita Real: R$ %{y:.2f}'
))

fig_forecast.add_trace(go.Scatter(
    x=df_forecast['Mês'],
    y=df_forecast['Receita Prevista'],
    mode='lines+markers',
    name='Receita Prevista',
    line=dict(color='green', width=2, dash='dash'),
    marker=dict(size=6),
    hovertemplate='Receita Prevista: R$ %{y:.2f}'
))

# Configurar o layout do gráfico
fig_forecast.update_layout(
    xaxis_title="Meses",
    yaxis_title="Receita (R$)",
    hovermode="x unified",
    margin=dict(l=0, r=0, t=50, b=0),
    legend_title_text='Receita'
)

# Exibir o gráfico de previsão
st.plotly_chart(fig_forecast, use_container_width=True)

# **ANÁLISE DE SENSIBILIDADE**
st.markdown("### Análise de Sensibilidade")

# Parâmetros ajustáveis pelo usuário
st.markdown("#### Parâmetros da Análise de Sensibilidade")
col1, col2 = st.columns(2)
with col1:
    taxa_crescimento_otimista = st.slider(
        "Taxa de Crescimento Mensal Otimista (%)",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.5
    )
with col2:
    taxa_crescimento_pessimista = st.slider(
        "Taxa de Crescimento Mensal Pessimista (%)",
        min_value=-20.0,
        max_value=0.0,
        value=-5.0,
        step=0.5
    )

# Aplicar as taxas de crescimento às receitas
df_receita_sensibilidade = df_receita.copy()

# Receita Otimista
df_receita_sensibilidade['Receita Otimista'] = df_receita['Receita Total'] * (1 + taxa_crescimento_otimista / 100) ** np.arange(len(df_receita))

# Receita Pessimista
df_receita_sensibilidade['Receita Pessimista'] = df_receita['Receita Total'] * (1 + taxa_crescimento_pessimista / 100) ** np.arange(len(df_receita))

# Criar o gráfico com as três linhas
fig_sensibilidade = go.Figure()

# Receita Original
fig_sensibilidade.add_trace(go.Scatter(
    x=df_receita['Mês'],
    y=df_receita['Receita Total'],
    mode='lines+markers',
    name='Receita Original',
    line=dict(color='blue', width=2),
    marker=dict(size=6),
    hovertemplate='Receita Original: R$ %{y:.2f}'
))

# Receita Otimista
fig_sensibilidade.add_trace(go.Scatter(
    x=df_receita_sensibilidade['Mês'],
    y=df_receita_sensibilidade['Receita Otimista'],
    mode='lines+markers',
    name='Receita Otimista',
    line=dict(color='green', width=2, dash='dash'),
    marker=dict(size=6),
    hovertemplate='Receita Otimista: R$ %{y:.2f}'
))

# Receita Pessimista
fig_sensibilidade.add_trace(go.Scatter(
    x=df_receita_sensibilidade['Mês'],
    y=df_receita_sensibilidade['Receita Pessimista'],
    mode='lines+markers',
    name='Receita Pessimista',
    line=dict(color='red', width=2, dash='dot'),
    marker=dict(size=6),
    hovertemplate='Receita Pessimista: R$ %{y:.2f}'
))

# Configurar o layout do gráfico
fig_sensibilidade.update_layout(
    xaxis_title="Meses",
    yaxis_title="Receita (R$)",
    hovermode="x unified",
    margin=dict(l=0, r=0, t=50, b=0),
    legend_title_text='Cenários'
)

# Exibir o gráfico de sensibilidade
st.plotly_chart(fig_sensibilidade, use_container_width=True)


### TABELA TOTAL DE VENDAS, RECEITA E PERCENTUAIS
# Cálculo do total de vendas por mês
df['Total Vendas'] = df[['Integral'] + conf_prest_cols].sum(axis=1)

# Cálculo da receita de Novas Vendas (vendas integrais + 1ª parcela de diluídas)
df_novas_vendas = df_receita['Receita - Integral'].copy()
for m in conf_prest_meses:
    col_name = f'Conf. Prest. ({m}m)'
    df_novas_vendas += df[col_name] / m

# Cálculo da receita de Vendas Legado (parcelas de vendas anteriores)
df_vendas_legado = df_receita['Receita Total'] - df_novas_vendas

# Cálculo dos percentuais
df_novas_vendas_percent = (df_novas_vendas / df_receita['Receita Total']) * 100
df_vendas_legado_percent = (df_vendas_legado / df_receita['Receita Total']) * 100

# Renomear 'Saldo Contábil' para 'Receita Futura Vendas'
receita_futura_vendas = df['Total Vendas'] - df_novas_vendas

# Cálculo do novo Saldo Contábil
saldo_contabil = []
s_prev = 0  # Saldo Contábil do mês anterior, inicia em zero

for t in range(len(df)):
    receita_vendas_legado_t = df_vendas_legado.iloc[t]
    total_vendas_t = df['Total Vendas'].iloc[t]
    receita_novas_vendas_t = df_novas_vendas.iloc[t]
    s_t = (s_prev - receita_vendas_legado_t) + (total_vendas_t - receita_novas_vendas_t)
    saldo_contabil.append(s_t)
    s_prev = s_t  # Atualiza o saldo para o próximo mês

saldo_contabil = pd.Series(saldo_contabil)

# Cálculo do % de GMV convertido
df_percent_gmv_convertido = (df_novas_vendas / df['Total Vendas']) * 100

# Criar um DataFrame para os totais
df_totais_mensal = pd.DataFrame({
    'Total de Vendas': df['Total Vendas'],
    'Total de Receita': df_receita['Receita Total'],
    'Receita Novas Vendas': df_novas_vendas,
    'Receita Vendas Legado': df_vendas_legado,
    'Receita Futura Vendas': receita_futura_vendas,
    'Saldo Contábil': saldo_contabil,
    '% Novas Vendas': df_novas_vendas_percent,
    '% Vendas Legado': df_vendas_legado_percent,
    '% de GMV convertido': df_percent_gmv_convertido
}).T

# Atribuir nomes dos meses como colunas
df_totais_mensal.columns = df_receita['Mês']

# Formatar os valores monetários e percentuais
df_totais_mensal_formatado = df_totais_mensal.copy()
for index in ['Total de Vendas', 'Total de Receita', 'Receita Novas Vendas', 'Receita Vendas Legado', 'Receita Futura Vendas', 'Saldo Contábil']:
    df_totais_mensal_formatado.loc[index] = df_totais_mensal_formatado.loc[index].apply(moeda_format)
for index in ['% Novas Vendas', '% Vendas Legado', '% de GMV convertido']:
    df_totais_mensal_formatado.loc[index] = df_totais_mensal_formatado.loc[index].apply(lambda x: f'{x:.2f}%')

# Exibir a tabela de totais
st.markdown("#### Total de Vendas, Receita e Percentuais por Mês")
st.dataframe(df_totais_mensal_formatado)

# Transpor a tabela de receita para colocar os meses como colunas e os tipos de reconhecimento como linhas
df_receita_transposta = df_receita.set_index('Mês').T

# Formatação dos valores monetários após a transposição
df_receita_transposta_formatado = df_receita_transposta.applymap(moeda_format)

# Exibir a tabela de receita transposta
st.markdown("#### Receita por Tipo de Reconhecimento")
st.dataframe(df_receita_transposta_formatado)