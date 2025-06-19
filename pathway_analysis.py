# Placeholder note: The full update will include
# 1. Real KEGG mapping using g:Profiler
# 2. Completion scores from KEGG pathway size
# 3. Pathway name resolution
# 4. Better visuals
# This script will be updated in the next stage of implementation.
# Stay tuned for the complete integrated code.

from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash_table
import pandas as pd
import plotly.express as px
import base64
import io
import plotly.io as pio
import numpy as np
import requests

# Layout remains same for upload and controls
pathway_analysis_layout = html.Div([
    html.H2("🧬 KEGG-Based Pathway Prediction from Multi-Omics Data", style={'color': 'white'}),
    html.Div([
        html.H4("Upload Multi-Omics Dataset (Transcriptomics, Metabolomics, Lipidomics with Group column)", style={'color': 'white'}),
        dcc.Upload(id='upload-pathway-data',
                   children=html.Div(['📂 Drag and Drop or Select File']),
                   style={'backgroundColor': '#add8e6', 'padding': '15px', 'textAlign': 'center'},
                   multiple=False),
        html.Div(id='uploaded-pathway-filename', style={'color': 'lightyellow', 'marginTop': '10px'}),
        html.Br(),
        html.Label("Select Organism:", style={'color': 'white'}),
        dcc.Dropdown(id='organism-select', options=[
            {'label': 'Human (hsa)', 'value': 'hsapiens'},
            {'label': 'Mouse (mmu)', 'value': 'mmusculus'},
            {'label': 'Zebrafish (dre)', 'value': 'drerio'}
        ], value='hsapiens', style={'width': '50%'}),
        html.Br(),
        dbc.Button("Run KEGG Pathway Prediction", id='run-pathway', color='primary')
    ]),
    html.Br(),
    html.Div(id='detected-omics-type', style={'color': 'white', 'fontWeight': 'bold'}),
    html.Div(id='pathway-output'),
    html.Div(id='pathway-plot'),
    html.Div(id='pathway-map-preview'),
    html.Div(id='pathway-download-section')
])

import gprofiler

def register_pathway_callbacks(app):
    @app.callback(
        Output('uploaded-pathway-filename', 'children'),
        Input('upload-pathway-data', 'filename'),
        prevent_initial_call=True
    )
    def update_filename(name):
        return f"✅ Uploaded File: {name}"

    @app.callback(
        Output('pathway-output', 'children'),
        Output('pathway-plot', 'children'),
        Output('pathway-map-preview', 'children'),
        Output('pathway-download-section', 'children'),
        Input('run-pathway', 'n_clicks'),
        State('upload-pathway-data', 'contents'),
        State('upload-pathway-data', 'filename'),
        State('organism-select', 'value'),
        prevent_initial_call=True
    )
    def analyze_pathway(n, contents, filename, organism):
        if not contents:
            return "❌ No file uploaded", None, None, None

        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

            if 'Group' not in df.columns:
                return "❌ 'Group' column is required.", None, None, None

            df[df.columns.difference(['SampleID', 'Group'])] = df[df.columns.difference(['SampleID', 'Group'])].apply(pd.to_numeric, errors='coerce')
            df.dropna(inplace=True)

            groups = df['Group'].unique()
            if len(groups) != 2:
                return "❌ Exactly two groups are required", None, None, None

            group1 = df[df['Group'] == groups[0]].drop(columns=['SampleID', 'Group'])
            group2 = df[df['Group'] == groups[1]].drop(columns=['SampleID', 'Group'])
            diff = group2.mean() - group1.mean()
            significant = diff[abs(diff) > 1.0]
            significant_ids = significant.index.tolist()

            from gprofiler import GProfiler
            gp = GProfiler(return_dataframe=True)
            result = gp.profile(organism=organism, query=significant_ids)
            if result.empty:
                return "⚠️ No significant pathways found.", None, None, None

            result = result[result['source'] == 'KEGG']
            result['completion'] = (result['intersection_size'] / result['term_size']) * 100
            result = result.sort_values('p_value').head(15)

            plot = px.bar(result, x='name', y='completion', color='p_value', text='intersection_size',
                          title='KEGG Pathway Completion %', labels={'name': 'Pathway Name'}, height=500)
            fig_path = "pathway_enrichment.png"
            pio.write_image(plot, fig_path)
            result.to_csv("pathway_enrichment_table.csv", index=False)

            table = dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in ['name', 'p_value', 'term_size', 'intersection_size', 'completion']],
                data=result.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'color': 'black'},
                style_header={'backgroundColor': 'navy', 'color': 'white', 'fontWeight': 'bold'}
            )

            badges = []
            for _, row in result.iterrows():
                path = row['name'].lower()
                if "parkinson" in path:
                    badges.append(html.Div([html.Span("🧠 Parkinson’s pathway detected!", style={'color': 'lime', 'fontWeight': 'bold'})]))
                if "alzheimer" in path:
                    badges.append(html.Div([html.Span("🧬 Alzheimer’s pathway enriched!", style={'color': 'aqua', 'fontWeight': 'bold'})]))

            preview_links = html.Div([
                html.Hr(),
                html.H3("🔗 KEGG Pathway Previews & External Links", style={'color': 'white'}),
                html.Ul([
                    html.Li([
                        html.A(f"{row['name']} (KEGG Page)", href=f"https://www.kegg.jp/pathway/{row.get('term_id', 'hsa00010')}", target="_blank"),
                        html.Br(),
                        html.Img(src=f"https://www.kegg.jp/kegg/pathway/{row.get('term_id', row.get('native', 'hsa00010'))}.png", style={"maxWidth": "100%", "marginBottom": "20px"})
                    ]) for _, row in result.iterrows()
                ])
            ])

            download_buttons = html.Div([
                dbc.Button("Download Plot (PNG)", id="btn-dl-png", color="info"),
                dcc.Download(id="dl-png"),
                html.Br(), html.Br(),
                dbc.Button("Download CSV Table", id="btn-dl-csv", color="secondary"),
                dcc.Download(id="dl-csv")
            ])

            return html.Div([table] + badges), dcc.Graph(figure=plot), preview_links, download_buttons

        except Exception as e:
            return f"❌ Error: {str(e)}", None, None, None

    

    

    @app.callback(
        Output("dl-png", "data"),
        Input("btn-dl-png", "n_clicks"),
        prevent_initial_call=True
    )
    def send_png(n):
        return dcc.send_file("pathway_enrichment.png")

    @app.callback(
        Output("dl-csv", "data"),
        Input("btn-dl-csv", "n_clicks"),
        prevent_initial_call=True
    )
    def send_csv(n):
        return dcc.send_file("pathway_enrichment_table.csv")

