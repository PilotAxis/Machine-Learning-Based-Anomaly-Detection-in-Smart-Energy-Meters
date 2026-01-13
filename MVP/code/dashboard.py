import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import os

# Paths to CSV files generated earlier
TELEMETRY_CSV = "/Users/ahmedmajid/Desktop/Digital-Twin-for Smart-Energy-Meters/digital-twin-mvp/data/meter.csv"
EDGE_CSV = "/Users/ahmedmajid/Desktop/Digital-Twin-for Smart-Energy-Meters/digital-twin-mvp/data/edge_health.csv"

app = dash.Dash(__name__)

app.layout = html.Div(style={"background-color": "#121212", "color": "white", "min-height": "100vh"}, children=[
    html.Div(
        style={
            "background-color": "#1F1F1F",
            "padding": "12px",
            "font-size": "22px",
            "font-weight": "bold",
            "border-bottom": "1px solid #000",
            "text-align": "center"
        },
        children="⚡ Smart Energy Meter Digital Twin"
    ),

    html.Div(style={
        "display": "flex",
        "flex-direction": "row"
    }, children=[
        html.Div(style={
            "width": "18%",
            "background-color": "#1A1A1A",
            "padding": "20px",
            "border-right": "1px solid #000",
            "min-height": "90vh"
        }, children=[
            html.H3("Navigation", style={"color": "white"}),
            html.Hr(style={"border-color": "#555"}),
            html.Div("• Live Telemetry", style={"margin": "10px 0"}),
            html.Div("• Alerts", style={"margin": "10px 0"}),
            html.Div("• Health Index", style={"margin": "10px 0"}),
            html.Div("• Predictive Insights", style={"margin": "10px 0"}),
        ]),

        html.Div(style={"width": "82%", "padding": "10px"}, children=[
            # PLACEHOLDER FOR MAIN DASH CONTENT — move the alert-box and graphs here
            html.Div(id="alert-box", style={
                "background-color": "#1A1A1A",
                "color": "#FFD65C",
                "border": "0px",
                "padding": "18px",
                "font-size": "20px",
                "font-weight": "600",
                "border-radius": "6px",
                "letter-spacing": "0.5px"
            }),

            html.Div([
                dcc.Graph(id="mhi-gauge"),
                dcc.Graph(id="live-temperature"),
                dcc.Graph(id="live-vibration"),
                dcc.Graph(id="live-pressure"),
                dcc.Graph(id="live-mhi")
            ])
        ])
    ]),

    dcc.Interval(
        id="update-interval",
        interval=3000,   # refresh every 3 seconds
        n_intervals=0
    ),
])

# ----------------------- CALLBACK ------------------------------

@app.callback(
    [
        Output("alert-box", "children"),
        Output("alert-box", "style"),
        Output("mhi-gauge", "figure"),
        Output("live-temperature", "figure"),
        Output("live-vibration", "figure"),
        Output("live-pressure", "figure"),
        Output("live-mhi", "figure")
    ],
    [Input("update-interval", "n_intervals")]
)
def update_graphs(n):

    if not os.path.exists(TELEMETRY_CSV) or not os.path.exists(EDGE_CSV):
        empty_fig = go.Figure()
        return "Waiting for data...", {"background-color": "#FFF3CD", "color": "#AD7A00"}, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    df = pd.read_csv(TELEMETRY_CSV)
    edge = pd.read_csv(EDGE_CSV)

    # Convert timestamps
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    if "timestamp" in edge.columns:
        edge["timestamp"] = pd.to_datetime(edge["timestamp"])

    # Latest values
    latest_temp = df["temperature"].iloc[-1]
    latest_vib = df["vibration"].iloc[-1]
    latest_pres = df["pressure"].iloc[-1]
    latest_anomaly = edge["ml_anomaly"].iloc[-1]
    latest_mhi = edge["MHI"].iloc[-1]

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=latest_mhi,
        title={"text": "Health Index"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "green"},
            "bgcolor": "#222",
            "borderwidth": 1,
            "bordercolor": "#555",
            "steps": [
                {"range": [0, 40], "color": "#3A0D0D"},
                {"range": [40, 60], "color": "#4E3B0C"},
                {"range": [60, 100], "color": "#1B3A2A"}
            ]
        }
    ))
    fig_gauge.update_layout(template="plotly_dark")

    # ---------------- GRAPHS ----------------

    # Temperature chart
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["temperature"],
        mode="lines+markers",
        name="Temperature"
    ))
    fig_temp.update_layout(title="Temperature Over Time", xaxis_title="Time", yaxis_title="°C")
    fig_temp.update_layout(template="plotly_dark")

    # Vibration chart
    fig_vib = go.Figure()
    fig_vib.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["vibration"],
        mode="lines+markers",
        name="Vibration"
    ))
    fig_vib.update_layout(title="Vibration (mm/s)", xaxis_title="Time", yaxis_title="mm/s")
    fig_vib.update_layout(template="plotly_dark")

    # Pressure chart
    fig_pres = go.Figure()
    fig_pres.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["pressure"],
        mode="lines+markers",
        name="Pressure"
    ))
    fig_pres.update_layout(title="Pressure (kPa)", xaxis_title="Time", yaxis_title="kPa")
    fig_pres.update_layout(template="plotly_dark")

    # MHI chart
    fig_mhi = go.Figure()
    fig_mhi.add_trace(go.Scatter(
        x=df["timestamp"],
        y=edge["MHI"],
        mode="lines+markers",
        name="MHI",
        line=dict(color="green")
    ))
    fig_mhi.update_layout(title="Meter Health Index (0–100)", xaxis_title="Time", yaxis_title="Health Score")
    fig_mhi.update_layout(template="plotly_dark")

    # ---------------- ALERT LOGIC ----------------

    alerts = []

    # Sensor alerts
    if latest_temp > 70:
        alerts.append("🔥 HIGH TEMPERATURE DETECTED")

    if latest_vib > 2.0:
        alerts.append("🌀 HIGH VIBRATION DETECTED")

    if latest_pres < 95 or latest_pres > 115:
        alerts.append("⚠️ PRESSURE OUT OF SAFE RANGE")

    # ML anomaly alert
    if latest_anomaly == 1:
        alerts.append("🤖 ML MODEL DETECTED AN ANOMALY")

    # MHI alerts
    if latest_mhi < 40:
        alerts.append("🛑 CRITICAL MHI — MAINTENANCE REQUIRED")
    elif latest_mhi < 60:
        alerts.append("⚠️ LOW MHI — POTENTIAL FAILURE RISK")

    # Determine alert box style
    if len(alerts) == 0:
        alert_msg = "✅ All Systems Normal"
        alert_style = {"background-color": "#001F14", "color": "#44FFB0", "border": "0px"}
    else:
        alert_msg = " | ".join(alerts)
        if "🛑" in alert_msg:
            alert_style = {"background-color": "#290000", "color": "#FF4444", "border": "0px"}
        elif "⚠️" in alert_msg:
            alert_style = {"background-color": "#2F2400", "color": "#FFCC66", "border": "0px"}
        else:
            alert_style = {"background-color": "#1A1A1A", "color": "#FFAA55", "border": "0px"}

    return alert_msg, alert_style, fig_gauge, fig_temp, fig_vib, fig_pres, fig_mhi


# ----------------------- RUN APP ------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=8050)