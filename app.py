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

# Wczytywanie konfiguracji Tinybird
with open('data-project/.tinyb') as tb:
    data = json.load(tb)
    tb_token = data['token']
    tb_host = data['host']

tb_client = tinybird.Client(token=tb_token, api=tb_host)


# Funkcja do pobierania danych z Tinybird i przetwarzania
def fetch_and_process_data(pipe_name, time_column, sum_column):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data[time_column])
    data = data.sort_values(by=['minuta'])
    data['suma_skumulowana'] = data.groupby('placowka')[sum_column].cumsum()
    return data


app.layout = html.Div([
    html.H1("Wybierz placówkę"),
    dcc.Dropdown(
        id='placowka-dropdown',
        options=[],  # Opcje zostaną uzupełnione po pierwszym załadowaniu danych
        value=None,  # Domyślnie brak wybranej placówki
        placeholder="Wybierz placówkę",
        clearable=True
    ),
    dcc.Interval(
        id='interval-component',
        interval=1200000,  # co 3 sekundy
        n_intervals=0
    ),
    html.H1("Liczba przeprowadzonych operacji w klinikach medycznych"),
    dcc.Graph(id='bar-chart-operacje', config={'displayModeBar': True}),
    html.H1("Liczba przyjętych pacjentów w klinikach medycznych"),
    dcc.Graph(id='pie-chart-pacjenci', config={'displayModeBar': True}),
])


@app.callback(
    [Output('bar-chart-operacje', 'figure'),
     Output('pie-chart-pacjenci', 'figure'),
     Output('placowka-dropdown', 'options')],
    [Input('interval-component', 'n_intervals'),
     Input('placowka-dropdown', 'value')]
)
def update_charts(n_intervals, selected_placowka):
    # Pobrane dane
    data_operacje = fetch_and_process_data('liczba_operacji', 'minuta', 'suma_przeprowadzonych_operacji')
    data_pacjenci = fetch_and_process_data('liczba_pacjentow', 'minuta', 'suma_przyjetych_pacjentow')

    # Aktualizacja listy placówek
    placowki = data_operacje['placowka'].unique()
    dropdown_options = [{'label': placowka, 'value': placowka} for placowka in placowki]

    if selected_placowka:
        filtered_operacje = data_operacje[data_operacje['placowka'] == selected_placowka]
        filtered_pacjenci = data_pacjenci[data_pacjenci['placowka'] == selected_placowka]
    else:
        filtered_operacje = data_operacje
        filtered_pacjenci = data_pacjenci

    # Przygotowanie danych dla wykresu słupkowego
    bar_data = filtered_operacje.groupby('placowka')['suma_przeprowadzonych_operacji'].sum().reset_index()

    fig_operacje = px.bar(
        bar_data,
        x='placowka',
        y='suma_przeprowadzonych_operacji',
        title='Liczba przeprowadzonych operacji w klinikach medycznych',
        labels={'suma_przeprowadzonych_operacji': 'Łączna liczba operacji', 'placowka': 'Placówka'},
        template=None  # Wyłączenie domyślnego szablonu
    )

    fig_operacje.update_layout(
        xaxis_title='Placówka',
        yaxis_title='Łączna liczba operacji',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych dla wykresu kołowego
    pie_data = filtered_pacjenci.groupby('placowka')['suma_skumulowana'].sum().reset_index()

    fig_pacjenci = px.pie(
        pie_data,
        names='placowka',
        values='suma_skumulowana',
        title='Liczba przyjętych pacjentów w klinikach medycznych',
        template=None  # Wyłączenie domyślnego szablonu
    )

    return fig_operacje, fig_pacjenci, dropdown_options


if __name__ == '__main__':
    app.run_server(debug=True)
