import dash
from dash import html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import matlab.engine
import threading

# Dash App initialisieren
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# MATLAB Engine starten (im Hintergrundthread)
eng = matlab.engine.start_matlab()

# Layout mit Überschrift, Start-Button und Z/Y-Auswahl in einer Zeile
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Electrical Impedance Tomography Control Center",
                        className="text-center text-primary mb-4"), width=12)
    ]),

    dbc.Row([
        dbc.Col(dbc.Button("Start Measurement", id="start-button", color="primary"), width="auto"),
        dbc.Col(
            dbc.ButtonGroup([
                dbc.Button("Z: Impedance", id="z-button", color="secondary", outline=True, n_clicks=0),
                dbc.Button("Y: Admittance", id="y-button", color="secondary", outline=True, n_clicks=0)
            ], id="zy-toggle", className="ms-3"), width="auto"
        )
    ], className="mb-4 align-items-center"),

    dbc.Row([
        dbc.Col(html.Div(id="status-output"), width=12)
    ])
], fluid=True)

# Callback zum Ausführen des MATLAB-Skripts bei Button-Klick + Erkennung Z/Y
@app.callback(
    Output("status-output", "children"),
    Input("start-button", "n_clicks"),
    State("z-button", "n_clicks"),
    State("y-button", "n_clicks"),
    prevent_initial_call=True
)
def start_measurement(n_clicks_start, n_clicks_z, n_clicks_y):
    selected_mode = "Z" if n_clicks_z > n_clicks_y else "Y"

    def run_matlab_script():
        eng.eval("Measurement_Script_new", nargout=0)

    thread = threading.Thread(target=run_matlab_script)
    thread.start()

    return f"Measurement started via MATLAB. Selection: {selected_mode}"

# App starten
if __name__ == '__main__':
    app.run(debug=True)
