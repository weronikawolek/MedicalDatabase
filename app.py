from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from verdin import tinybird
import json
import concurrent.futures

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

server = app.server


# Function to initialize Tinybird Client
def initialize_tb_client():
    with open('data-project/.tinyb') as tb:
        data = json.load(tb)
        tb_token = data['token']
        tb_host = data['host']
    return tinybird.Client(token=tb_token, api=tb_host)


# Fetch and process data from Tinybird
def fetch_and_process_data(tb_client, pipe_name, time_column, sum_column):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data[time_column])
    data = data.sort_values(by=['minuta'])
    data['suma_skumulowana'] = data.groupby('placowka')[sum_column].cumsum()
    return data


# Fetch and process average hospitalization time data
def fetch_and_process_avg_hospitalization(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data


# Fetch and process average waiting time data
def fetch_and_process_avg_waiting_time(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data



app.layout = html.Div([
    html.H1("Wybierz placówkę"),
    dcc.Dropdown(
        id='placowka-dropdown',
        options=[],  # Options will be populated after initial data load
        value=None,  # Default value
        placeholder="Wybierz placówkę",
        clearable=True
    ),
    dcc.Interval(
        id='interval-component',
        interval=1200000,  # Every 20 minutes
        n_intervals=0
    ),
    html.H1("Liczba przeprowadzonych operacji w klinikach medycznych"),
    dcc.Graph(id='bar-chart-operacje', config={'displayModeBar': True}),
    html.H1("Liczba przyjętych pacjentów w klinikach medycznych"),
    dcc.Graph(id='pie-chart-pacjenci', config={'displayModeBar': True}),
    html.H1("Liczba nagłych wypadków w klinikach medycznych"),
    dcc.Graph(id='scatter-chart-nagle-przypadki', config={'displayModeBar': True}),
    html.H1("Średni czas hospitalizacji w klinikach medycznych"),
    dcc.Graph(id='heatmap-hospitalizacja', config={'displayModeBar': True}),
    html.H1("Średni czas oczekiwania na wizytę w klinikach medycznych"),
    dcc.Graph(id='line-chart-oczekiwanie', config={'displayModeBar': True}),
])


@app.callback(
    [Output('bar-chart-operacje', 'figure'),
     Output('pie-chart-pacjenci', 'figure'),
     Output('scatter-chart-nagle-przypadki', 'figure'),
     Output('heatmap-hospitalizacja', 'figure'),
     Output('line-chart-oczekiwanie', 'figure'),
     Output('placowka-dropdown', 'options')],
    [Input('interval-component', 'n_intervals'),
     Input('placowka-dropdown', 'value')]
)
def update_charts(n_intervals, selected_placowka):
    tb_client = initialize_tb_client()

    # Use concurrent.futures to fetch data in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_operacje = executor.submit(fetch_and_process_data, tb_client, 'liczba_operacji', 'minuta', 'suma_przeprowadzonych_operacji')
        future_pacjenci = executor.submit(fetch_and_process_data, tb_client, 'liczba_pacjentow', 'minuta', 'suma_przyjetych_pacjentow')
        future_nagle_przypadki = executor.submit(fetch_and_process_data, tb_client, 'liczba_naglych_przypadkow', 'minuta', 'suma_naglych_przypadkow')
        future_hospitalizacja = executor.submit(fetch_and_process_avg_hospitalization, tb_client, 'sredni_czas_hospitalizacji')
        future_oczekiwanie = executor.submit(fetch_and_process_avg_waiting_time, tb_client, 'sredni_czas_oczekiwania_na_wizyte')

        data_operacje = future_operacje.result()
        data_pacjenci = future_pacjenci.result()
        data_nagle_przypadki = future_nagle_przypadki.result()
        data_hospitalizacja = future_hospitalizacja.result()
        data_oczekiwanie = future_oczekiwanie.result()

    # Update dropdown options
    placowki = data_operacje['placowka'].unique()
    dropdown_options = [{'label': placowka, 'value': placowka} for placowka in placowki]

    # Filter data based on selected placowka
    if selected_placowka:
        filtered_operacje = data_operacje[data_operacje['placowka'] == selected_placowka]
        filtered_pacjenci = data_pacjenci[data_pacjenci['placowka'] == selected_placowka]
        filtered_nagle_przypadki = data_nagle_przypadki[data_nagle_przypadki['placowka'] == selected_placowka]
        filtered_hospitalizacja = data_hospitalizacja[data_hospitalizacja['placowka'] == selected_placowka]
        filtered_oczekiwanie = data_oczekiwanie[data_oczekiwanie['placowka'] == selected_placowka]
    else:
        filtered_operacje = data_operacje
        filtered_pacjenci = data_pacjenci
        filtered_nagle_przypadki = data_nagle_przypadki
        filtered_hospitalizacja = data_hospitalizacja
        filtered_oczekiwanie = data_oczekiwanie

    # Bar chart data preparation
    bar_data = filtered_operacje.groupby('placowka')['suma_przeprowadzonych_operacji'].sum().reset_index()

    fig_operacje = px.bar(
        bar_data,
        x='placowka',
        y='suma_przeprowadzonych_operacji',
        title='Liczba przeprowadzonych operacji w klinikach medycznych',
        labels={'suma_przeprowadzonych_operacji': 'Łączna liczba operacji', 'placowka': 'Placówka'},
        template='plotly_white'
    )

    fig_operacje.update_layout(
        xaxis_title='Placówka',
        yaxis_title='Łączna liczba operacji',
        legend_title='Placówka',
        hovermode='x'
    )

    # Pie chart data preparation
    pie_data = filtered_pacjenci.groupby('placowka')['suma_skumulowana'].sum().reset_index()

    fig_pacjenci = px.pie(
        pie_data,
        names='placowka',
        values='suma_skumulowana',
        title='Liczba przyjętych pacjentów w klinikach medycznych',
        template='plotly_white'
    )

    # Scatter plot with lines for emergency cases
    scatter_data = filtered_nagle_przypadki.groupby(['minuta', 'placowka'])[
        'suma_naglych_przypadkow'].sum().reset_index()

    fig_nagle_przypadki = px.scatter(
        scatter_data,
        x='minuta',
        y='suma_naglych_przypadkow',
        color='placowka',
        title='Liczba nagłych wypadków w klinikach medycznych',
        labels={'suma_naglych_przypadkow': 'Liczba nagłych wypadków', 'minuta': 'Minuta'},
        template='plotly_white'
    )

    fig_nagle_przypadki.update_traces(mode='lines+markers')

    fig_nagle_przypadki.update_layout(
        xaxis_title='Czas',
        yaxis_title='Liczba nagłych wypadków',
        legend_title='Placówka',
        hovermode='x'
    )

    # Heatmap for average hospitalization time
    heatmap_data = filtered_hospitalizacja.pivot(index='minuta', columns='placowka',
                                                 values='sredni_czas_hospitalizacji')

    bar_hospitalizacja = px.bar(
        heatmap_data.transpose(),  # Transpose data for correct orientation
        barmode='group',
        title='Średni czas hospitalizacji w klinikach medycznych',
        labels={'value': 'Średni czas hospitalizacji (minuty)', 'index': 'Placówka', 'variable': 'Czas'},
        template='plotly_white'
    )

    bar_hospitalizacja.update_layout(
        xaxis_title='Placówka',
        yaxis_title='Średni czas hospitalizacji (minuty)',
        legend_title='Czas',
        hovermode='x'
    )

    # Line chart for average waiting time
    line_data = filtered_oczekiwanie.groupby(['minuta', 'placowka'])[
        'sredni_czas_oczekiwania_na_wizyte'].mean().reset_index()

    scatter_oczekiwanie = px.scatter(
        line_data,
        x='minuta',
        y='sredni_czas_oczekiwania_na_wizyte',
        color='placowka',
        title='Średni czas oczekiwania na wizytę w klinikach medycznych',
        labels={'sredni_czas_oczekiwania_na_wizyte': 'Średni czas oczekiwania (minuty)', 'minuta': 'Czas'},
        template='plotly_white'
    )

    scatter_oczekiwanie.update_layout(
        xaxis_title='Czas',
        yaxis_title='Średni czas oczekiwania (minuty)',
        legend_title='Placówka',
        hovermode='x'
    )

    return fig_operacje, fig_pacjenci, fig_nagle_przypadki, bar_hospitalizacja, scatter_oczekiwanie, dropdown_options


if __name__ == '__main__':
    app.run_server(debug=True)
