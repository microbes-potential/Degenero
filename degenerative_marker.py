from dash import dcc, html, Input, Output, State, dash_table
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import ttest_ind
import utils
import plotly.io as pio

# Layout for Degenerative Marker Detection
degenerative_marker_layout = html.Div([
    html.H1("🧠 Degenerative Marker Detection", style={'textAlign': 'center', 'color': 'white'}),
    html.Hr(),

    dcc.Upload(
        id='upload-marker-data',
        children=html.Div(['📂 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '100%', 'height': '80px', 'lineHeight': '80px',
            'borderWidth': '2px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'backgroundColor': '#343a40', 'color': 'white'
        },
        multiple=False
    ),
    html.Div(id='uploaded-file-name', style={'color': 'white', 'textAlign': 'center', 'marginTop': '10px'}),
    html.Br(),

    html.Div([
        html.Label("p-value Threshold", style={'color': 'white'}),
        dcc.Slider(id='pval-thresh', min=0, max=0.1, step=0.005, value=0.05, tooltip={"placement": "bottom", "always_visible": True})
    ]),
    html.Br(),

    html.Div([
        html.Label("Fold Change Threshold", style={'color': 'white'}),
        dcc.Slider(id='fc-thresh', min=1, max=5, step=0.1, value=2.0, tooltip={"placement": "bottom", "always_visible": True})
    ]),
    html.Br(),

    dbc.Button("🔍 Identify Markers", id='run-marker-analysis', color="danger", style={'width': '100%'}),
    html.Br(), html.Br(),

    html.Div(id='marker-volcano-plot'),
    html.Br(),
    html.Div(id='marker-output'),
    html.Div(id='download-marker-section')
])

# Callback registration
def register_degenerative_marker_callbacks(app):

    @app.callback(
        Output('uploaded-file-name', 'children'),
        Input('upload-marker-data', 'contents'),
        State('upload-marker-data', 'filename'),
        prevent_initial_call=True
    )
    def show_uploaded_name(contents, filename):
        if contents and filename:
            return f"✅ Uploaded file: {filename}"
        return ""

    @app.callback(
        Output('marker-output', 'children'),
        Output('marker-volcano-plot', 'children'),
        Output('download-marker-section', 'children'),
        Input('run-marker-analysis', 'n_clicks'),
        State('upload-marker-data', 'contents'),
        State('upload-marker-data', 'filename'),
        State('pval-thresh', 'value'),
        State('fc-thresh', 'value'),
        prevent_initial_call=True
    )
    def run_marker_analysis(n, contents, filename, p_thresh, fc_thresh):
        if contents is None or filename is None:
            return "❌ No file uploaded.", None, None

        df = utils.parse_uploaded_file(contents, filename)
        df[df.columns.difference(['Group'])] = df[df.columns.difference(['Group'])].apply(pd.to_numeric, errors='coerce')

        if 'Group' not in df.columns:
            return "❌ 'Group' column missing in data.", None, None

        try:
            features = df.drop(columns=['Group'])
            group_labels = df['Group'].unique()
            if len(group_labels) != 2:
                return "❌ Exactly 2 groups required for comparison.", None, None

            g1 = df[df['Group'] == group_labels[0]]
            g2 = df[df['Group'] == group_labels[1]]

            pvals, fold_changes = [], []
            for col in features.columns:
                stat, pval = ttest_ind(g1[col], g2[col], equal_var=False, nan_policy='omit')
                fc = (g1[col].mean() + 1e-6) / (g2[col].mean() + 1e-6)
                pvals.append(pval)
                fold_changes.append(fc)

            log_fc = np.log2(fold_changes)
            log_p = -np.log10(pvals)
            regulation = [
                'Up' if p < p_thresh and lfc > np.log2(fc_thresh) else
                'Down' if p < p_thresh and lfc < -np.log2(fc_thresh) else
                'NS'
                for p, lfc in zip(pvals, log_fc)
            ]

            result_df = pd.DataFrame({
                'Feature': features.columns,
                'p-value': pvals,
                'Fold Change': fold_changes,
                'log2(FC)': log_fc,
                '-log10(p)': log_p,
                'Regulation': regulation
            })

            color_map = {'Up': 'red', 'Down': 'blue', 'NS': 'gray'}
            fig = px.scatter(result_df, x='log2(FC)', y='-log10(p)',
                             color='Regulation', color_discrete_map=color_map,
                             hover_name='Feature', title='Volcano Plot')
            fig.update_layout(
                template='plotly_white', font=dict(size=14),
                title_font=dict(size=18), height=600, width=800
            )

            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in result_df.columns],
                data=result_df[result_df['Regulation'] != 'NS'].to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={"textAlign": "left"}
            )

            volcano_download_buttons = html.Div([
                html.Hr(),
                html.H4("⬇️ Download Volcano Plot"),
                dbc.Button("Download PNG", id="btn-download-volcano-png", color="secondary", style={'marginRight': '10px'}),
                dbc.Button("Download PDF", id="btn-download-volcano-pdf", color="secondary", style={'marginRight': '10px'}),
                dbc.Button("Download SVG", id="btn-download-volcano-svg", color="secondary"),
                dcc.Download(id="download-volcano-png"),
                dcc.Download(id="download-volcano-pdf"),
                dcc.Download(id="download-volcano-svg")
            ])

            download_ui = html.Div([
                html.Hr(),
                html.H4("⬇️ Download Marker Table"),
                dbc.Button("Download Marker Table", id="btn-download-markers", color="info"),
                dcc.Download(id="download-marker-csv")
            ])

            return table, html.Div([dcc.Graph(figure=fig), volcano_download_buttons]), download_ui

        except Exception as e:
            return f"❌ Error in analysis: {str(e)}", None, None

    @app.callback(Output("download-marker-csv", "data"),
                  Input("btn-download-markers", "n_clicks"),
                  State('upload-marker-data', 'contents'),
                  State('upload-marker-data', 'filename'),
                  State('pval-thresh', 'value'),
                  State('fc-thresh', 'value'),
                  prevent_initial_call=True)
    def download_marker_table(n, contents, filename, p_thresh, fc_thresh):
        df = utils.parse_uploaded_file(contents, filename)
        df[df.columns.difference(['Group'])] = df[df.columns.difference(['Group'])].apply(pd.to_numeric, errors='coerce')
        features = df.drop(columns=['Group'])
        group_labels = df['Group'].unique()
        g1 = df[df['Group'] == group_labels[0]]
        g2 = df[df['Group'] == group_labels[1]]

        pvals, fold_changes = [], []
        for col in features.columns:
            stat, pval = ttest_ind(g1[col], g2[col], equal_var=False, nan_policy='omit')
            fc = (g1[col].mean() + 1e-6) / (g2[col].mean() + 1e-6)
            pvals.append(pval)
            fold_changes.append(fc)

        log_fc = np.log2(fold_changes)
        regulation = [
            'Up' if p < p_thresh and lfc > np.log2(fc_thresh) else
            'Down' if p < p_thresh and lfc < -np.log2(fc_thresh) else
            'NS'
            for p, lfc in zip(pvals, log_fc)
        ]

        result_df = pd.DataFrame({
            'Feature': features.columns,
            'p-value': pvals,
            'Fold Change': fold_changes,
            'log2(FC)': log_fc,
            '-log10(p)': -np.log10(pvals),
            'Regulation': regulation
        })

        return dcc.send_data_frame(result_df.to_csv, filename='degenerative_markers.csv', index=False)

    @app.callback(Output("download-volcano-png", "data"), Input("btn-download-volcano-png", "n_clicks"), prevent_initial_call=True)
    def download_png(n):
        fig = pio.read_json(fig.to_json())
        pio.write_image(fig, "volcano_plot.png", scale=3)
        return dcc.send_file("volcano_plot.png")

    @app.callback(Output("download-volcano-pdf", "data"), Input("btn-download-volcano-pdf", "n_clicks"), prevent_initial_call=True)
    def download_pdf(n):
        fig = pio.read_json(fig.to_json())
        pio.write_image(fig, "volcano_plot.pdf", scale=3)
        return dcc.send_file("volcano_plot.pdf")

    @app.callback(Output("download-volcano-svg", "data"), Input("btn-download-volcano-svg", "n_clicks"), prevent_initial_call=True)
    def download_svg(n):
        fig = pio.read_json(fig.to_json())
        pio.write_image(fig, "volcano_plot.svg", scale=3)
        return dcc.send_file("volcano_plot.svg")
