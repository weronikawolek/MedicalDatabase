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
    data[time_column] = pd.to_datetime(data[time_column])
    data = data.sort_values(by=[time_column])
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


# Pobieranie i przetwarzanie danych o średnim czasie wizyty
def fetch_and_process_avg_visit_time(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data


# Pobieranie i przetwarzanie danych o dostępnym sprzęcie medycznym
def fetch_and_process_medical_equipment(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data


# Pobieranie i przetwarzanie danych o personelu medycznym
def fetch_and_process_medical_staff(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data


# Pobieranie i przetwarzanie danych o dostępnych wolnych łóżkach
def fetch_and_process_free_beds(tb_client, pipe_name):
    response = tb_client.pipe(pipe_name).query()
    data = pd.json_normalize(response.data)
    data['minuta'] = pd.to_datetime(data['minuta'])
    data = data.sort_values(by=['minuta'])
    return data

# Layout aplikacji
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("DOSTĘP DO USŁUG MEDYCZNYCH W CZASIE RZECZYWISTYM", style={'color': 'LightBlue', 'font-family': 'Georgia', 'font-weight': 'bold'}, className='text-center'), width=12),
        #dbc.Col(html.P("Strona stworzona przez Julię Kordek, Weronikę Wołek oraz Matyldę Lange.", style={'color': 'LightPink', 'font-family': 'Georgia', 'font-weight': 'normal', 'text-align': 'right', 'display': 'flex', 'justify-content': 'right', 'align-items': 'right', 'height': '20px'}, className='text-center'), width=20),
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
        interval=3000,  # Co 3 s
        n_intervals=0
    ),
    dbc.Row([dbc.Col([dcc.Graph(id='bar-chart-pacjenci', config={'displayModeBar': False})], width=12)]),
    dbc.Row([dbc.Col([dcc.Graph(id='bar-chart-nagle-przypadki', config={'displayModeBar': False})], width=12)]),  # Zmieniony wykres
    dbc.Row([dbc.Col([dcc.Graph(id='pie-chart-operacje', config={'displayModeBar': False})], width=6, style={'min-height': '400px', 'padding': '10px'}),
             dbc.Col([dcc.Graph(id='pie-chart-zabiegi', config={'displayModeBar': False})], width=6, style={'min-height': '400px', 'padding': '10px'})]),
    dbc.Row([
        dbc.Col([dcc.Graph(id='line-chart-hospitalizacja', config={'displayModeBar': False})], width=6),  # Wykres liniowy
        dbc.Col([dcc.Graph(id='line-chart-czas-wizyty', config={'displayModeBar': False})], width=6)  # Wykres liniowy
    ]),
    dbc.Row([dbc.Col([dcc.Graph(id='line-chart-oczekiwanie', config={'displayModeBar': False})], width=12)]),  # Przesunięty wykres
    dbc.Row([dbc.Col([dcc.Graph(id='bar-chart-sprzet', config={'displayModeBar': False})], width=12)]),  # Nowy wykres słupkowy
    dbc.Row([dbc.Col([dcc.Graph(id='bar-chart-personel', config={'displayModeBar': False})], width=12)]),  # Nowy poziomy wykres słupkowy
    dbc.Row([dbc.Col([dcc.Graph(id='scatter-chart-lozka', config={'displayModeBar': False})], width=12)])  # Nowy wykres punktowy
], fluid=True)

# Deklaracja komponentów na stronie
@app.callback(
    [Output('bar-chart-pacjenci', 'figure'), # Pionowy wykres słupkowy
     Output('bar-chart-nagle-przypadki', 'figure'), # Poziomy wykres słupkowy
     Output('pie-chart-operacje', 'figure'), # Wykres kołowy
     Output('pie-chart-zabiegi', 'figure'), # Wykres kołowy
     Output('line-chart-hospitalizacja', 'figure'),  # Wykres liniowy
     Output('line-chart-czas-wizyty', 'figure'),  # Wykres liniowy
     Output('line-chart-oczekiwanie', 'figure'), # Wykres liniowy
     Output('bar-chart-sprzet', 'figure'),  # Pionowy wykres słupkowy
     Output('bar-chart-personel', 'figure'),  # Poziomy wykres słupkowy
     Output('scatter-chart-lozka', 'figure'),  # Wykres punktowy
     Output('placowka-dropdown', 'options')], # Filtrowanie placówek
    [Input('interval-component', 'n_intervals'),
     Input('placowka-dropdown', 'value')]
)

# Aktualizowanie wykresów w czasie rzeczywistym zgodnie z zadeklarowaną wartością interwału
def update_charts(n_intervals, selected_placowka):
    tb_client = initialize_tb_client()

    # Użycie concurrent.futures do równoległego pobierania danych
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_pacjenci = executor.submit(fetch_and_process_data, tb_client, 'liczba_pacjentow', 'minuta', 'suma_przyjetych_pacjentow')
        future_operacje = executor.submit(fetch_and_process_data, tb_client, 'liczba_operacji', 'minuta', 'suma_przeprowadzonych_operacji')
        future_nagle_przypadki = executor.submit(fetch_and_process_data, tb_client, 'liczba_naglych_przypadkow', 'minuta', 'suma_naglych_przypadkow')
        future_hospitalizacja = executor.submit(fetch_and_process_avg_hospitalization, tb_client, 'sredni_czas_hospitalizacji')
        future_oczekiwanie = executor.submit(fetch_and_process_avg_waiting_time, tb_client, 'sredni_czas_oczekiwania_na_wizyte')
        future_zabiegi = executor.submit(fetch_and_process_procedures, tb_client, 'liczba_wykonanych_zabiegow')
        future_czas_wizyty = executor.submit(fetch_and_process_avg_visit_time, tb_client, 'sredni_czas_wizyty')
        future_sprzet = executor.submit(fetch_and_process_medical_equipment, tb_client, 'sprzet_medyczny')
        future_personel = executor.submit(fetch_and_process_medical_staff, tb_client, 'personel_medyczny')
        future_lozka = executor.submit(fetch_and_process_free_beds, tb_client, 'dostepne_lozka')  # Nowa funkcja do pobierania danych o wolnych łóżkach

        data_pacjenci = future_pacjenci.result()
        data_operacje = future_operacje.result()
        data_nagle_przypadki = future_nagle_przypadki.result()
        data_hospitalizacja = future_hospitalizacja.result()
        data_oczekiwanie = future_oczekiwanie.result()
        data_zabiegi = future_zabiegi.result()
        data_czas_wizyty = future_czas_wizyty.result()
        data_sprzet = future_sprzet.result()
        data_personel = future_personel.result()
        data_lozka = future_lozka.result()  # Przetworzone dane o wolnych łóżkach

    # Aktualizacja opcji dropdown
    placowki = data_operacje['placowka'].unique()
    dropdown_options = [{'label': placowka, 'value': placowka} for placowka in placowki]

    # Filtrowanie danych na podstawie wybranej placówki
    if selected_placowka:
        filtered_pacjenci = data_pacjenci[data_pacjenci['placowka'] == selected_placowka]
        filtered_operacje = data_operacje[data_operacje['placowka'] == selected_placowka]
        filtered_nagle_przypadki = data_nagle_przypadki[data_nagle_przypadki['placowka'] == selected_placowka]
        filtered_hospitalizacja = data_hospitalizacja[data_hospitalizacja['placowka'] == selected_placowka]
        filtered_oczekiwanie = data_oczekiwanie[data_oczekiwanie['placowka'] == selected_placowka]
        filtered_zabiegi = data_zabiegi[data_zabiegi['placowka'] == selected_placowka]
        filtered_czas_wizyty = data_czas_wizyty[data_czas_wizyty['placowka'] == selected_placowka]
        filtered_sprzet = data_sprzet[data_sprzet['placowka'] == selected_placowka]
        filtered_personel = data_personel[data_personel['placowka'] == selected_placowka]
        filtered_lozka = data_lozka[data_lozka['placowka'] == selected_placowka]  # Filtracja danych o wolnych łóżkach
    else:
        filtered_pacjenci = data_pacjenci
        filtered_operacje = data_operacje
        filtered_nagle_przypadki = data_nagle_przypadki
        filtered_hospitalizacja = data_hospitalizacja
        filtered_oczekiwanie = data_oczekiwanie
        filtered_zabiegi = data_zabiegi
        filtered_czas_wizyty = data_czas_wizyty
        filtered_sprzet = data_sprzet
        filtered_personel = data_personel
        filtered_lozka = data_lozka  # Dane o wolnych łóżkach bez filtra

    # Przygotowanie danych do wykresu pionowego słupkowego o ilości pacjentów
    bar_data = filtered_pacjenci.groupby('placowka')['suma_przyjetych_pacjentow'].sum().reset_index()

    fig_pacjenci = px.bar(
        bar_data,
        x='placowka',
        y='suma_przyjetych_pacjentow',
        labels={'suma_przyjetych_pacjentow': 'Łączna liczba pacjentów', 'placowka': 'Placówka'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel1
    )

    fig_pacjenci.update_layout(
        title={'text': 'Liczba przyjętych pacjentów w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Placówka',
        yaxis_title='Łączna liczba pacjentów',
        legend_title='Placówka',
        hovermode='x'
    )
    fig_pacjenci.update_traces(marker_color='LightPink')

    # Przygotowanie danych do wykresu poziomego słupkowego o ilości nagłych przypadków
    bar_nagle_przypadki_data = filtered_nagle_przypadki.groupby('placowka')['suma_naglych_przypadkow'].sum().reset_index()

    fig_nagle_przypadki = px.bar(
        bar_nagle_przypadki_data,
        y='placowka',
        x='suma_naglych_przypadkow',
        labels={'suma_naglych_przypadkow': 'Liczba nagłych przypadków', 'placowka': 'Placówka'},
        template='plotly_white',
        orientation='h',
        color_discrete_sequence=px.colors.qualitative.Pastel2
    )

    fig_nagle_przypadki.update_layout(
        title={'text': 'Liczba nagłych przypadków w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Liczba nagłych przypadków',
        yaxis_title='Placówka',
        legend_title='Placówka',
        hovermode='y'
    )
    fig_nagle_przypadki.update_traces(marker_color='LightBlue')

    # Przygotowanie danych do wykresu kołowego o ilości przeprowadzonych operacji
    pie_data = filtered_operacje.groupby('placowka')['suma_skumulowana'].sum().reset_index()

    fig_operacje = px.pie(
        pie_data,
        names='placowka',
        values='suma_skumulowana',
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel2
    )

    fig_operacje.update_traces(textinfo='value')

    fig_operacje.update_layout(
        title={'text': 'Liczba przeprowadzonych operacji w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}}
    )

    # Przygotowanie danych do wykresu kołowego o ilości wykonanych zabiegów
    pie_data_zabiegi = filtered_zabiegi.groupby('placowka')['suma_wykonanych_zabiegow'].sum().reset_index()

    fig_zabiegi = px.pie(
        pie_data_zabiegi,
        names='placowka',
        values='suma_wykonanych_zabiegow',
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel1
    )

    fig_zabiegi.update_traces(textinfo='value')

    fig_zabiegi.update_layout(
        title={'text': 'Liczba wykonanych zabiegów w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}}
    )

    # Przygotowanie danych do wykresu liniowego o średnim czasie hospitalizacji
    line_hospitalizacja_data = filtered_hospitalizacja.groupby(['minuta', 'placowka'])[
        'sredni_czas_hospitalizacji'].mean().reset_index()

    fig_hospitalizacja = px.line(
        line_hospitalizacja_data,
        x='minuta',
        y='sredni_czas_hospitalizacji',
        color='placowka',
        labels={'sredni_czas_hospitalizacji': 'Średni czas hospitalizacji (dni)', 'minuta': 'Czas'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel1  # Niestandardowa sekwencja kolorów
    )

    fig_hospitalizacja.update_layout(
        title={'text': 'Średni czas hospitalizacji w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Czas',
        yaxis_title='Średni czas hospitalizacji (dni)',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu liniowego o średnim czasie wizyty
    line_czas_wizyty_data = filtered_czas_wizyty.groupby(['minuta', 'placowka'])[
        'sredni_czas_wizyty'].mean().reset_index()

    fig_czas_wizyty = px.line(
        line_czas_wizyty_data,
        x='minuta',
        y='sredni_czas_wizyty',
        color='placowka',
        labels={'sredni_czas_wizyty': 'Średni czas wizyty (minuty)', 'minuta': 'Czas'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel2
    )

    fig_czas_wizyty.update_layout(
        title={'text': 'Średni czas wizyty w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Czas',
        yaxis_title='Średni czas wizyty (minuty)',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu liniowego o średnim czasie oczekiwania na wizytę
    line_data = filtered_oczekiwanie.groupby(['minuta', 'placowka'])[
        'sredni_czas_oczekiwania_na_wizyte'].mean().reset_index()

    fig_oczekiwanie = px.line(
        line_data,
        x='minuta',
        y='sredni_czas_oczekiwania_na_wizyte',
        color='placowka',
        labels={'sredni_czas_oczekiwania_na_wizyte': 'Średni czas oczekiwania (dni)', 'minuta': 'Czas'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel2
    )

    fig_oczekiwanie.update_layout(
        title={'text': 'Średni czas oczekiwania na wizytę w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Czas',
        yaxis_title='Średni czas oczekiwania (dni)',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu pionowego słupkowego o ilości dostępnego sprzętu medycznego
    bar_sprzet_data = filtered_sprzet.groupby('placowka')['dostepny_sprzet_medyczny'].sum().reset_index()

    fig_sprzet = px.bar(
        bar_sprzet_data,
        x='placowka',
        y='dostepny_sprzet_medyczny',
        labels={'dostepny_sprzet_medyczny': 'Dostępny sprzęt medyczny', 'placowka': 'Placówka'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel1
    )

    fig_sprzet.update_layout(
        title={'text': 'Dostępny sprzęt medyczny w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Placówka',
        yaxis_title='Dostępny sprzęt medyczny',
        legend_title='Placówka',
        hovermode='x'
    )

    # Przygotowanie danych do wykresu poziomego słupkowego o ilości dostępnego personelu medycznego
    bar_personel_data = filtered_personel.groupby('placowka')['personel_medyczny'].sum().reset_index()

    fig_personel = px.bar(
        bar_personel_data,
        y='placowka',
        x='personel_medyczny',
        labels={'personel_medyczny': 'Personel medyczny', 'placowka': 'Placówka'},
        template='plotly_white',
        orientation='h',
        color_discrete_sequence=px.colors.qualitative.Pastel2
    )

    fig_personel.update_layout(
        title={'text': 'Personel medyczny w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Personel medyczny',
        yaxis_title='Placówka',
        legend_title='Placówka',
        hovermode='y'
    )

    # Przygotowanie danych do wykresu punktowego o ilości dostępnych łóżek
    scatter_lozka_data = filtered_lozka.groupby(['minuta', 'placowka'])[
        'suma_dostepnych_lozek'].sum().reset_index()

    fig_lozka = px.scatter(
        scatter_lozka_data,
        x='minuta',
        y='suma_dostepnych_lozek',
        color='placowka',
        labels={'suma_dostepnych_lozek': 'Dostępne wolne łóżka', 'minuta': 'Czas'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Pastel1
    )

    fig_lozka.update_layout(
        title={'text': 'Dostępne wolne łóżka w klinikach medycznych', 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'darkgrey', 'family': 'Georgia'}},
        xaxis_title='Czas',
        yaxis_title='Dostępne wolne łóżka',
        legend_title='Placówka',
        hovermode='x'
    )

    return fig_pacjenci, fig_nagle_przypadki, fig_operacje, fig_zabiegi, fig_hospitalizacja, fig_czas_wizyty, fig_oczekiwanie, fig_sprzet, fig_personel, fig_lozka, dropdown_options


if __name__ == '__main__':
    app.run_server(debug=True)
