from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from verdin import tinybird
import json
import concurrent.futures

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

server = app.server

# Funkcja inicjalizująca klienta Tinybird
def initialize_tb_client():
    with open('data-project/.tinyb') as tb:
        data = json.load(tb)
        tb_token = data['token']
        tb_host = data['host']
    return tinybird.Client(token=tb_token, api=tb_host)

# Pobieranie i przetwarzanie danych z Tinybird
def fetch_and_process_data(tb_client, pipe_name, time_column, sum_column):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data[time_column])
    data = data.sort_values(by=['minuta'])
    data['suma_skumulowana'] = data.groupby('placowka')[sum_column].cumsum()
    return data

# Pobieranie i przetwarzanie danych o średnim czasie hospitalizacji
def fetch_and_process_avg_hospitalization(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data

# Pobieranie i przetwarzanie danych o średnim czasie oczekiwania
def fetch_and_process_avg_waiting_time(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data

# Pobieranie i przetwarzanie danych o liczbie wykonanych zabiegów
def fetch_and_process_procedures(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Wybierz placówkę", className='text-center'), width=12),
        dbc.Col(dcc.Dropdown(
            id='placowka-dropdown',
            options=[],  # Opcje będą zaktualizowane po inicjalnym załadowaniu danych
            value=None,  # Domyślna wartość
            placeholder="Wybierz placówkę",
            clearable=True
        ), width=12),
    ]),
    dcc.Interval(
        id='interval-component',
        interval=1200000,  # Co 20 minut
        n_intervals=0
    ),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-chart-operacje', config={'displayModeBar': True})
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='pie-chart-pacjenci', config={'displayModeBar': True}),
        ], width=6, style={'min-height': '400px', 'padding': '10px'}),
        dbc.Col([
            dcc.Graph(id='pie-chart-zabiegi', config={'displayModeBar': True}),
        ], width=6, style={'min-height': '400px', 'padding': '10px'})
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='scatter-chart-nagle-przypadki', config={'displayModeBar': True})
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-chart-hospitalizacja', config={'displayModeBar': True})
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='line-chart-oczekiwanie', config={'displayModeBar': True})
        ], width=12)
    ])
], fluid=True)

@app.callback(
    [Output('bar-chart-operacje', 'figure'),
     Output('pie-chart-pacjenci', 'figure'),
     Output('pie-chart-zabiegi', 'figure'),
     Output('scatter-chart-nagle-przypadki', 'figure'),
     Output('bar-chart-hospitalizacja', 'figure'),
     Output('line-chart-oczekiwanie', 'figure'),
     Output('placowka-dropdown', 'options')],
    [Input('interval-component', 'n_intervals'),
     Input('placowka-dropdown', 'value')]
)
def update_charts(n_intervals, selected_placowka):
    tb_client = initialize_tb_client()

    # Użycie concurrent.futures do równoległego pobierania danych
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_operacje = executor.submit(fetch_and_process_data, tb_client, 'liczba_operacji', 'minuta', 'suma_przeprowadzonych_operacji')
        future_pacjenci = executor.submit(fetch_and_process_data, tb_client, 'liczba_pacjentow', 'minuta', 'suma_przyjetych_pacjentow')
        future_nagle_przypadki = executor.submit(fetch_and_process_data, tb_client, 'liczba_naglych_przypadkow', 'minuta', 'suma_naglych_przypadkow')
        future_hospitalizacja = executor.submit(fetch_and_process_avg_hospitalization, tb_client, 'sredni_czas_hospitalizacji')
        future_oczekiwanie = executor.submit(fetch_and_process_avg_waiting_time, tb_client, 'sredni_czas_oczekiwania_na_wizyte')
        future_zabiegi = executor.submit(fetch_and_process_procedures, tb_client, 'liczba_wykonanych_zabiegow')

        data_operacje = future_operacje.result()
        data_pacjenci = future_pacjenci.result()
        data_nagle_przypadki = future_nagle_przypadki.result()
        data_hospitalizacja = future_hospitalizacja.result()
        data_oczekiwanie = future_oczekiwanie.result()
        data_zabiegi = future_zabiegi.result()

    # Aktualizacja opcji dropdown
    placowki = data_operacje['placowka'].unique()
    dropdown_options = [{'label': placowka, 'value': placowka} for placowka in placowki]

    # Filtrowanie danych na podstawie wybranej placówki
    if selected_placowka:
        filtered_operacje = data_operacje[data_operacje['placowka'] == selected_placowka]
        filtered_pacjenci = data_pacjenci[data_pacjenci['placowka'] == selected_placowka]
        filtered_nagle_przypadki = data_nagle_przypadki[data_nagle_przypadki['placowka'] == selected_placowka]
        filtered_hospitalizacja = data_hospitalizacja[data_hospitalizacja['placowka'] == selected_placowka]
        filtered_oczekiwanie = data_oczekiwanie[data_oczekiwanie['placowka'] == selected_placowka]
        filtered_zabiegi = data_zabiegi[data_zabiegi['placowka'] == selected_placowka]
    else:
        filtered_operacje = data_operacje
        filtered_pacjenci = data_pacjenci
        filtered_nagle_przypadki = data_nagle_przypadki
        filtered_hospitalizacja = data_hospitalizacja
        filtered_oczekiwanie = data_oczekiwanie
        filtered_zabiegi = data_zabiegi

    # Przygotowanie danych do wykresów
    bar_data = filtered_operacje.groupby('placowka')['suma_przeprowadzonych_operacji'].sum().reset_index()

    fig_operacje = px.bar(
        bar_data,
        x='placowka',
        y='suma_przeprowadzonych_operacji',
        labels={'suma_przeprowadzonych_operacji': 'Łączna liczba operacji', 'placowka': 'Placówka'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Plotly  # Niestandardowa sekwencja kolorów
    )

    fig_operacje.update_layout(
        title={'text': 'Liczba przeprowadzonych operacji w klinikach medycznych', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Placówka',
        yaxis_title='Łączna liczba operacji',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu kołowego dla pacjentów
    pie_data = filtered_pacjenci.groupby('placowka')['suma_skumulowana'].sum().reset_index()

    fig_pacjenci = px.pie(
        pie_data,
        names='placowka',
        values='suma_skumulowana',
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Set1  # Niestandardowa sekwencja kolorów
    )

    fig_pacjenci.update_traces(textinfo='value')  # Wyświetlanie tylko liczby

    fig_pacjenci.update_layout(
        title={'text': 'Liczba przyjętych pacjentów w klinikach medycznych', 'x': 0.5, 'xanchor': 'center'}
    )

    # Przygotowanie danych do wykresu kołowego dla zabiegów
    pie_data_zabiegi = filtered_zabiegi.groupby('placowka')['suma_wykonanych_zabiegow'].sum().reset_index()

    fig_zabiegi = px.pie(
        pie_data_zabiegi,
        names='placowka',
        values='suma_wykonanych_zabiegow',
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Plotly # Niestandardowa sekwencja kolorów
    )

    fig_zabiegi.update_traces(textinfo='value')  # Wyświetlanie tylko liczby

    fig_zabiegi.update_layout(
        title={'text': 'Liczba wykonanych zabiegów w klinikach medycznych', 'x': 0.5, 'xanchor': 'center'}
    )

    # Przygotowanie danych do wykresu punktowego dla nagłych wypadków
    scatter_data = filtered_nagle_przypadki.groupby(['minuta', 'placowka'])[
        'suma_naglych_przypadkow'].sum().reset_index()

    fig_nagle_przypadki = px.scatter(
        scatter_data,
        x='minuta',
        y='suma_naglych_przypadkow',
        color='placowka',
        labels={'suma_naglych_przypadkow': 'Liczba nagłych wypadków', 'minuta': 'Minuta'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Dark2  # Niestandardowa sekwencja kolorów
    )

    fig_nagle_przypadki.update_traces(mode='lines+markers')

    fig_nagle_przypadki.update_layout(
        title={'text': 'Liczba nagłych wypadków w klinikach medycznych', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Czas',
        yaxis_title='Liczba nagłych wypadków',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu słupkowego dla średniego czasu hospitalizacji
    heatmap_data = filtered_hospitalizacja.pivot(index='minuta', columns='placowka',
                                                 values='sredni_czas_hospitalizacji')

    bar_hospitalizacja = px.bar(
        heatmap_data.transpose(),  # Transponowanie danych dla poprawnej orientacji
        barmode='group',
        labels={'value': 'Średni czas hospitalizacji (minuty)', 'index': 'Placówka', 'variable': 'Czas'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Prism  # Niestandardowa sekwencja kolorów
    )

    bar_hospitalizacja.update_layout(
        title={'text': 'Średni czas hospitalizacji w klinikach medycznych', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Placówka',
        yaxis_title='Średni czas hospitalizacji (minuty)',
        legend_title='Czas',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu liniowego dla średniego czasu oczekiwania
    line_data = filtered_oczekiwanie.groupby(['minuta', 'placowka'])[
        'sredni_czas_oczekiwania_na_wizyte'].mean().reset_index()

    scatter_oczekiwanie = px.scatter(
        line_data,
        x='minuta',
        y='sredni_czas_oczekiwania_na_wizyte',
        color='placowka',
        labels={'sredni_czas_oczekiwania_na_wizyte': 'Średni czas oczekiwania (minuty)', 'minuta': 'Czas'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Set3  # Niestandardowa sekwencja kolorów
    )

    scatter_oczekiwanie.update_layout(
        title={'text': 'Średni czas oczekiwania na wizytę w klinikach medycznych', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Czas',
        yaxis_title='Średni czas oczekiwania (minuty)',
        legend_title='Placówka',
        hovermode='x'
    )

    return fig_operacje, fig_pacjenci, fig_zabiegi, fig_nagle_przypadki, bar_hospitalizacja, scatter_oczekiwanie, dropdown_options

if __name__ == '__main__':
    app.run_server(debug=True)
