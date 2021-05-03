import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
import json
from collections import defaultdict

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
state_path = "fake.json"

def convert_to_pd(state_history:dict, election_year="2021", baseline_year="2019"):
    data = defaultdict(list)
    # get political parties baseline
    baseline = {}
    for pparty, baseline_results in state_history[baseline_year][0]["results"].items():
        baseline[pparty] = baseline_results["seats"]
    for state in state_history[election_year]:
        data["perc_counted_votes"].append(state["perc_counted_votes"])
        data["time"].append(state["retrieval_time"])
        for pparty, individual_results in state["results"].items():
            data[f"seats_{pparty}"].append(individual_results["seats"])
            data[f"baseline_{pparty}"].append(baseline[pparty])
    return pd.DataFrame(data)


def get_df(path):
    with open(path) as fd:
        state = json.load(fd)
    df = convert_to_pd(state)
    # only select parties with at least one seat
    selected_columns = [col for col in df.columns if df[col].sum()]
    df = df[selected_columns]
    # need to reshape long
    df = pd.wide_to_long(df, ["seats", "baseline"], i="time", j="pparty", sep="_", suffix="\D+")
    return df.reset_index()



def get_df_by_blocks(path):
    df = get_df(path)
    mapping_to_blocks = {
        "PSOE": "Left",
        "PP": "Right",
        "Cs": "Center",
        "MÁS MADRID": "Left",
        "VOX": "Right",
        "PODEMOS-IU": "Left"
    }
    df["blocks"] = df["pparty"].map(mapping_to_blocks)
    df = df.groupby(["time", "blocks"]).sum().reset_index()
    # add center right block
    wide_df = df.pivot(index="time", columns="blocks")
    for col in wide_df.columns.levels[0]:
        wide_df[(col, "Center-Right")] = wide_df[(col, "Right")] + wide_df[(col, "Center")]
    df = wide_df.stack(level=1).reset_index()
    return df


app.layout = html.Div(children=[
    html.H1(children='Madrid Elections 2021'),

    html.Div(children='''
        Minimal Dash application to follow the Election Results
    '''),

    dcc.Graph(
        id='graph-pparties'
    ),
    dcc.Graph(
        id='graph-blocks'
    ),
    dcc.Interval(
        id='interval-component',
        interval=1*5000, # in milliseconds
        n_intervals=0
    )
])


@app.callback(
    Output('graph-pparties', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    df = get_df(state_path)
    fig = px.line(df, x="time", y="seats", color='pparty', hover_name="pparty",
                  hover_data={"baseline": True, "pparty": False, "time": False})
    fig.update_layout(hovermode="x")
    return fig


@app.callback(
    Output('graph-blocks', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    df = get_df_by_blocks(state_path)
    fig = px.line(df, x="time", y="seats", color='blocks', hover_name="blocks",
                  hover_data={"baseline": True, "blocks": False, "time": False})
    fig.update_layout(hovermode="x")
    return fig

if __name__ == '__main__':
    # df = get_df("fake.json")
    # df = get_df_by_blocks("fake.json")
    print("check in pycharm")
    app.run_server(debug=True)