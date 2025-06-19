from dash import dcc, html, Input, Output, State, dash_table
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import processing
import utils
import individual_analysis
import multiomics_integration
import degenerative_marker
import pathway_analysis

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
app.title = "DegenerOmics"
server = app.server

# Preprocessing layout
preprocessing_layout = html.Div([
    html.H2("Normalization", style={'color': 'white'}),
    dcc.Upload(id='upload-data', children=html.Div(['📂 Drag and Drop or ', html.A('Select File')]), style={'backgroundColor': '#90ee90', 'padding': '20px', 'textAlign': 'center'}, multiple=False),
    dcc.Dropdown(id='normalization-method', options=[
        {'label': 'Log2 (Transcriptomics)', 'value': 'log2'},
        {'label': 'Log10 (Metabolomics)', 'value': 'log10'},
        {'label': 'Z-score (Lipidomics)', 'value': 'zscore'}
    ], placeholder="Normalization Method"),
    dcc.RadioItems(id='missing-value-method', options=[
        {'label': 'Mean', 'value': 'mean'},
        {'label': 'Median', 'value': 'median'},
        {'label': 'Drop', 'value': 'drop'}
    ], labelStyle={'display': 'block', 'color': 'white'}),
    dbc.Button("Run Preprocessing", id='run-preprocessing', color='success'),
    html.Div(id='preprocessing-output'),
    html.Br(),
    html.Div(id='download-section')
])

# Documentation layout
documentation_layout = html.Div([
    html.H1("📚 Documentation", style={'textAlign': 'center', 'color': 'white'}),
    html.Hr(),
    html.H2("How to Use This App", style={'color': 'white'}),
    html.Ol([
        html.Li("Upload your datasets (.csv or .xlsx).", style={'color': 'white'}),
        html.Li("Complete preprocessing: normalization, missing value handling.", style={'color': 'white'}),
        html.Li("Run individual omics analysis.", style={'color': 'white'}),
        html.Li("Perform integrated analysis across omics layers.", style={'color': 'white'}),
        html.Li("Detect and visualize critical markers.", style={'color': 'white'})
    ]),
    html.Br(),
    html.P("Supported file types: .csv, .xlsx", style={'color': 'white'})
])

# Team layout
team_layout = html.Div([
    html.H1("👨‍🔬 Research Team", style={'textAlign': 'center', 'color': 'white'}),
    html.Hr(),
    html.Div([
        html.Img(src='/assets/prof.png', style={'height': '200px', 'borderRadius': '50%', 'display': 'block', 'marginLeft': 'auto', 'marginRight': 'auto'}),
        html.H3("Principal Investigator", style={'textAlign': 'center', 'color': 'white', 'marginTop': '20px'}),
        html.P("Dr. Marica Bakovic (Full Professor)", style={'textAlign': 'center', 'fontSize': '20px', 'color': 'white'}),
        html.P("Department of Human Health and Nutritional Sciences", style={'textAlign': 'center', 'color': 'white'}),
        html.P("University of Guelph, Guelph N1G 2W1, Canada", style={'textAlign': 'center', 'color': 'white'}),
        html.P("E-mail: mbakovic@uoguelph.ca", style={'textAlign': 'center', 'color': 'white'}),
        html.Hr(),
        html.H3("Researchers", style={'textAlign': 'left', 'color': 'white'}),
        html.Ul([
            html.Li(html.B("Asma Rafique"), style={'color': 'white'}),
            html.P("Postdoctoral Fellow", style={'marginLeft': '20px', 'color': 'white'}),
            html.Li(html.B("Roya Iraji"), style={'color': 'white'}),
            html.P("Graduate Student", style={'marginLeft': '20px', 'color': 'white'})
        ], style={'textAlign': 'left', 'listStylePosition': 'inside'}),
        html.Br(),
        html.P("For inquiries, please contact: mbakovic@uoguelph.ca", style={'textAlign': 'center', 'color': 'white', 'marginTop': '20px'})
    ])
])

# Home layout
home_layout = html.Div([
    html.H1("DegenerOmics", style={'textAlign': 'center', 'color': 'white'}),
    html.H4("Integrated Multi-Omics Marker Discovery for Parkinson’s and Alzheimer’s", style={'textAlign': 'center', 'color': '#d4d4d4'}),
    html.Hr(style={'borderColor': 'white'}),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Background")),
            dbc.CardBody(html.P("Neurodegenerative diseases such as Parkinson's and Alzheimer's involve complex molecular mechanisms spanning genomics, metabolomics, and lipidomics layers. Traditional single-omics studies fail to capture the complete picture."))
        ], color="dark", inverse=True), width=4),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Research Gap")),
            dbc.CardBody(html.P("Despite massive data availability, there is no unified statistical platform to integrate multi-omics datasets specifically aimed at discovering molecular markers for degenerative diseases."))
        ], color="info", inverse=True), width=4),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Introduction")),
            dbc.CardBody(html.P("DegenerOmics enables a stepwise, user-friendly, integrated analysis of transcriptomics, metabolomics, and lipidomics data to detect critical disease-associated markers."))
        ], color="success", inverse=True), width=4)
    ])
])

# App layout
app.layout = dbc.Container([
    html.A("🔝 Back to Top", href="#", style={"position": "fixed", "bottom": "30px", "right": "30px", "zIndex": 9999, "padding": "10px 15px", "backgroundColor": "#007bff", "color": "white", "borderRadius": "5px", "textDecoration": "none"}),
    dcc.Tabs(id="tabs", value='home', children=[
        dcc.Tab(label='Home', value='home'),
        dcc.Tab(label='Data Normalization', value='Data Normalization'),
        dcc.Tab(label='Individual Analysis', value='individual'),
        dcc.Tab(label='Multi-Omics Integration', value='integration'),
        dcc.Tab(label='Biomarker Detection', value='marker'),
	dcc.Tab(label='Pathway Analysis', value='pathway'),
        dcc.Tab(label='Documentation', value='documentation'),
        dcc.Tab(label='Research Team', value='team')
    ]),
    html.Div(id='tabs-content')
], fluid=True, style={'backgroundColor': '#013220', 'minHeight': '100vh'})

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab(tab):
    if tab == 'home':
        return home_layout
    elif tab == 'Data Normalization':
        return preprocessing_layout
    elif tab == 'individual':
        return individual_analysis.individual_analysis_layout
    elif tab == 'integration':
        return multiomics_integration.multiomics_integration_layout
    elif tab == 'marker':
        return degenerative_marker.degenerative_marker_layout
    elif tab == 'pathway':
        return pathway_analysis.pathway_analysis_layout
    elif tab == 'documentation':
        return documentation_layout
    elif tab == 'team':
        return team_layout
    return html.Div("Invalid tab")

@app.callback(
    Output('preprocessing-output', 'children'),
    Output('download-section', 'children'),
    Input('run-preprocessing', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('normalization-method', 'value'),
    State('missing-value-method', 'value'),
    prevent_initial_call=True
)
def run_preprocessing(n, contents, filename, norm, missing):
    if contents is None or filename is None:
        return "❌ No file uploaded.", None
    try:
        df = utils.parse_uploaded_file(contents, filename)
        df = processing.handle_missing_values(df, method=missing)
        if norm == 'log2':
            df = processing.normalize_transcriptomics(df)
        elif norm == 'log10':
            df = processing.normalize_metabolomics(df)
        elif norm == 'zscore':
            df = processing.normalize_lipidomics(df)
        else:
            return "⚠️ Please select a normalization method.", None

        table = dash_table.DataTable(columns=[{"name": i, "id": i} for i in df.columns], data=df.head(10).to_dict('records'))
        df.to_csv("preprocessed_output.csv", index=False)
        download_button = html.Div([
            html.Br(),
            html.Hr(),
            html.H4("⬇️ Download Processed Data"),
            dbc.Button("Download CSV", id="btn-download-preprocessed", color="info"),
            dcc.Download(id="download-preprocessed")
        ])
        return table, download_button
    except Exception as e:
        return f"❌ Error during preprocessing: {str(e)}", None

@app.callback(
    Output("download-preprocessed", "data"),
    Input("btn-download-preprocessed", "n_clicks"),
    prevent_initial_call=True
)
def generate_download(n_clicks):
    return dcc.send_file("preprocessed_output.csv")

individual_analysis.register_individual_analysis_callbacks(app)
multiomics_integration.register_multiomics_integration_callbacks(app)
degenerative_marker.register_degenerative_marker_callbacks(app)
pathway_analysis.register_pathway_callbacks(app)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8080, debug=True)

