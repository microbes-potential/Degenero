# individual_analysis.py

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import processing
import utils
import plotly.io as pio

# Layout for Individual Omics Analysis
individual_analysis_layout = html.Div([
    html.H1("🔬 Individual Omics Analysis", style={'textAlign': 'center', 'color': 'white'}),
    html.Hr(),

    dcc.Upload(
        id='upload-omics-data',
        children=html.Div(['📂 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '2px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'backgroundColor': '#90ee90', 'color': 'black'
        },
        multiple=False
    ),

    html.Br(),
    html.Div(id='uploaded-filename', style={'textAlign': 'center', 'color': 'white', 'fontSize': '16px'}),
    html.Br(),

    dbc.Button("🧪 Run Individual Analysis", id='run-individual-analysis', color="info", style={'width': '100%'}),
    html.Br(), html.Br(),

    html.Div(id='individual-analysis-output')
])

# Callback function for individual omics analysis
def register_individual_analysis_callbacks(app):
    
    @app.callback(
        Output('uploaded-filename', 'children'),
        Input('upload-omics-data', 'filename'),
        prevent_initial_call=True
    )
    def display_uploaded_filename(filename):
        if filename:
            return f"📁 Uploaded File: {filename}"
        return ""

    @app.callback(
        Output('individual-analysis-output', 'children'),
        Input('run-individual-analysis', 'n_clicks'),
        State('upload-omics-data', 'contents'),
        State('upload-omics-data', 'filename'),
        prevent_initial_call=True
    )
    def perform_individual_analysis(n_clicks, contents, filename):
        if contents is None:
            return "❌ No file uploaded."

        # Parse and preprocess the uploaded file
        df = utils.parse_uploaded_file(contents, filename)
        df = processing.normalize_transcriptomics(df)

        # Perform PCA
        pca_df = processing.perform_pca(df)

        # Create PCA plot with white background
        fig = px.scatter(pca_df, x='PC1', y='PC2',
                         title='PCA Plot - Individual Omics')
        fig.update_layout(template='none',
                          plot_bgcolor='white',
                          paper_bgcolor='white',
                          font=dict(color='black'),
                          title_font=dict(size=20))

        # Return both graph and download button
        return html.Div([
            dcc.Graph(id='pca-graph', figure=fig),
            html.Button("📥 Download PCA Plot", id="download-pca-btn", style={"marginTop": "10px"}),
            dcc.Download(id="pca-download")
        ])

    @app.callback(
        Output("pca-download", "data"),
        Input("download-pca-btn", "n_clicks"),
        State("pca-graph", "figure"),
        prevent_initial_call=True
    )
    def download_pca_plot(n_clicks, fig):
        return dcc.send_bytes(lambda buffer: pio.write_image(fig, buffer, format='png'), "PCA_plot.png")

