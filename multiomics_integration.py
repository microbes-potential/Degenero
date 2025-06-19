# multiomics_integration.py

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import processing
import utils

# Layout for Multi-Omics Integration
multiomics_integration_layout = html.Div([
    html.H1("🔗 Multi-Omics Integration", style={'textAlign': 'center', 'color': 'white'}),
    html.Hr(),

    html.H4("Upload Transcriptomics Dataset:", style={'color': 'white'}),
    dcc.Upload(
        id='upload-transcriptomics',
        children=html.Div(['📂 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '2px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'backgroundColor': '#90ee90', 'color': 'black'
        },
        multiple=False
    ),
    html.Div(id='transcriptomics-filename', style={'textAlign': 'center', 'color': 'white'}),
    html.Br(),

    html.H4("Upload Metabolomics Dataset:", style={'color': 'white'}),
    dcc.Upload(
        id='upload-metabolomics',
        children=html.Div(['📂 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '2px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'backgroundColor': '#90ee90', 'color': 'black'
        },
        multiple=False
    ),
    html.Div(id='metabolomics-filename', style={'textAlign': 'center', 'color': 'white'}),
    html.Br(),

    html.H4("Upload Lipidomics Dataset:", style={'color': 'white'}),
    dcc.Upload(
        id='upload-lipidomics',
        children=html.Div(['📂 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '2px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'backgroundColor': '#90ee90', 'color': 'black'
        },
        multiple=False
    ),
    html.Div(id='lipidomics-filename', style={'textAlign': 'center', 'color': 'white'}),
    html.Br(),

    dbc.Button("🔄 Integrate and Run PCA", id='run-integration', color="primary", style={'width': '100%', 'fontWeight':'bold', 'color': 'white'}),
    html.Br(), html.Br(),

    html.Div(id='integration-output')
])

# Callback registration
def register_multiomics_integration_callbacks(app):

    @app.callback(
        Output('transcriptomics-filename', 'children'),
        Input('upload-transcriptomics', 'filename'),
        prevent_initial_call=True
    )
    def show_transcriptomics_filename(filename):
        if filename:
            return f"📁 Uploaded: {filename}"
        return ""

    @app.callback(
        Output('metabolomics-filename', 'children'),
        Input('upload-metabolomics', 'filename'),
        prevent_initial_call=True
    )
    def show_metabolomics_filename(filename):
        if filename:
            return f"📁 Uploaded: {filename}"
        return ""

    @app.callback(
        Output('lipidomics-filename', 'children'),
        Input('upload-lipidomics', 'filename'),
        prevent_initial_call=True
    )
    def show_lipidomics_filename(filename):
        if filename:
            return f"📁 Uploaded: {filename}"
        return ""

    @app.callback(
        Output('integration-output', 'children'),
        Input('run-integration', 'n_clicks'),
        State('upload-transcriptomics', 'contents'),
        State('upload-transcriptomics', 'filename'),
        State('upload-metabolomics', 'contents'),
        State('upload-metabolomics', 'filename'),
        State('upload-lipidomics', 'contents'),
        State('upload-lipidomics', 'filename'),
        prevent_initial_call=True
    )
    def integrate_and_pca(n_clicks, trans_content, trans_filename,
                          metab_content, metab_filename,
                          lipid_content, lipid_filename):
        if None in [trans_content, metab_content, lipid_content]:
            return "⚠️ Please upload all three omics datasets."

        # Parse uploaded files
        df_trans = utils.parse_uploaded_file(trans_content, trans_filename)
        df_metab = utils.parse_uploaded_file(metab_content, metab_filename)
        df_lipid = utils.parse_uploaded_file(lipid_content, lipid_filename)

        # Normalize each omics layer
        df_trans = processing.normalize_transcriptomics(df_trans)
        df_metab = processing.normalize_metabolomics(df_metab)
        df_lipid = processing.normalize_lipidomics(df_lipid)

        # Merge all omics layers
        integrated_df = pd.concat([df_trans, df_metab, df_lipid], axis=1)

        # Perform PCA on integrated data
        pca_df = processing.perform_pca(integrated_df)

        # Create PCA scatter plot with white background
        fig = px.scatter(pca_df, x='PC1', y='PC2',
                         title='PCA Plot - Integrated Omics')
        fig.update_layout(template='none',
                          plot_bgcolor='white',
                          paper_bgcolor='white',
                          font=dict(color='black'),
                          title_font=dict(size=20))

        return html.Div([
            dbc.Alert("✅ Integration and PCA Completed Successfully!", color="success"),
            dcc.Graph(id='multi-pca-graph', figure=fig),
            html.Button("📥 Download PCA Plot", id="download-multi-pca-btn", style={"marginTop": "10px"}),
            dcc.Download(id="multi-pca-download")
        ])

    @app.callback(
        Output("multi-pca-download", "data"),
        Input("download-multi-pca-btn", "n_clicks"),
        State("multi-pca-graph", "figure"),
        prevent_initial_call=True
    )
    def download_multi_pca_plot(n_clicks, fig):
        return dcc.send_bytes(lambda b: pio.write_image(fig, b, format='png'), "Integrated_PCA_plot.png")

