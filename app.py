import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
from flask import Flask
import base64
import io
import plotly.express as px
import openai

# OpenAI API anahtarı (değiştirin)
openai.api_key = "sk-2AxvhgpNGs8QuWreYcxtJ0oZEcUJVgXgslnbgvIVAvT3BlbkFJYLeciXI-FsCtOsImqs0kuw6BP4m70on6aK4p1pS00A"

# Flask sunucusu
server = Flask(__name__)

# Dash uygulaması
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Uygulama layout'u
app.layout = html.Div(
    [
        dbc.Container(
            [
                html.H2("Veri Seti Yükleyici ve Özetleyici", style={"text-align": "center", "margin-top": "20px"}),
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(["Dosyayı buraya bırakın veya ", html.A("seçin")]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin-bottom": "20px",
                    },
                ),
                html.Div(id="output-data-upload"),
                html.Hr(),
                html.Div(id="openai-report",
                         style={"padding": "20px", "background-color": "#F7F7F7", "border-radius": "10px"}),
                html.Hr(),
                dbc.Row(id="stat-cards", className="mb-4"),
            ]
        )
    ]
)


# Dosya yükleme ve veri işleme
@app.callback(
    dash.dependencies.Output("output-data-upload", "children"),
    dash.dependencies.Output("stat-cards", "children"),
    dash.dependencies.Input("upload-data", "contents"),
    dash.dependencies.State("upload-data", "filename"),
)
def update_output(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        dashboard_content = generate_dashboard(df)
        cards_content = generate_stat_cards(df)
        return dashboard_content, cards_content
    return html.Div(), []


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        return df
    except Exception as e:
        return html.Div(['Dosya işlenirken hata oluştu.'])


# Dinamik olarak kartları oluştur
def generate_stat_cards(df):
    total_rows = len(df)
    total_columns = len(df.columns)
    first_column_unique = df[df.columns[0]].nunique()

    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Toplam Satır", className="card-title"),
                        html.P(f"{total_rows}", className="card-text"),
                    ]
                ),
                style={"background-color": "#4A90E2", "color": "white", "border-radius": "15px",
                       "box-shadow": "5px 5px 15px rgba(0,0,0,0.2)"}
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Toplam Sütun", className="card-title"),
                        html.P(f"{total_columns}", className="card-text"),
                    ]
                ),
                style={"background-color": "#50E3C2", "color": "white", "border-radius": "15px",
                       "box-shadow": "5px 5px 15px rgba(0,0,0,0.2)"}
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(f"{df.columns[0]} Benzersiz Değer", className="card-title"),
                        html.P(f"{first_column_unique}", className="card-text"),
                    ]
                ),
                style={"background-color": "#F5A623", "color": "white", "border-radius": "15px",
                       "box-shadow": "5px 5px 15px rgba(0,0,0,0.2)"}
            ),
            width=4,
        ),
    ]


# Grafiklerin oluşturulması
def generate_dashboard(df):
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=px.histogram(df, x=df.columns[0])), width=6),
                    dbc.Col(dcc.Graph(figure=px.scatter(df, x=df.columns[0], y=df.columns[1])), width=6),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=px.box(df, x=df.columns[0])), width=6),
                    dbc.Col(dcc.Graph(figure=px.line(df, x=df.columns[0], y=df.columns[1])), width=6),
                ]
            ),
        ]
    )


# OpenAI'dan rapor üretimi
@app.callback(
    dash.dependencies.Output("openai-report", "children"),
    dash.dependencies.Input("upload-data", "contents"),
    dash.dependencies.State("upload-data", "filename"),
)
def generate_summary_report(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        summary = generate_openai_report(df)
        return html.Div(summary, style={"padding": "20px", "background-color": "#E8F0FE", "border-radius": "10px"})
    return html.Div()


def generate_openai_report(df):
    prompt = f"Veri setini Türkçe olarak özetle: {df.describe()} ve veri setindeki temel içgörüleri açıkla."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Veri analizi konusunda uzmansın."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5,
    )
    report = response['choices'][0]['message']['content']
    report_lines = report.split("\n")
    formatted_report = []

    for line in report_lines:
        if line.strip():
            formatted_report.append(html.P(line.strip()))

    return formatted_report


if __name__ == "__main__":
    app.run_server(debug=True)
