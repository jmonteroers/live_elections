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
state_path = "state.json"


def get_counted_perc(path, election_year="2021"):
    last_update_time = get_last_update(path, election_year)
    with open(path) as fd:
        state_history = json.load(fd)
    for state in state_history[election_year]:
        if state["retrieval_time"] == last_update_time:
            return state["perc_counted_votes"]
    return 0.


def get_last_update(path, election_year="2021"):
    with open(path) as fd:
        state_history = json.load(fd)
    return max(state["retrieval_time"] for state in state_history[election_year])


def convert_to_pd(state_history:dict, election_year="2021", baseline_year="2019"):
    data = defaultdict(list)
    # get political parties baseline
    baseline = {}
    for pparty, baseline_results in state_history[baseline_year]["results"].items():
        baseline[pparty] = baseline_results["seats"]
    for state in state_history[election_year]:
        data["perc_counted_votes"].append(state["perc_counted_votes"])
        data["time"].append(state["retrieval_time"])
        for pparty, individual_results in state["results"].items():
            data[f"seats_{pparty}"].append(individual_results["seats"])
            data[f"percentage_{pparty}"].append(individual_results["perc_ballots"])
            data[f"baseline_{pparty}"].append(baseline.get(pparty, 0))
    return pd.DataFrame(data)


def get_df(path):
    with open(path) as fd:
        state = json.load(fd)
    df = convert_to_pd(state)
    # need to reshape long
    df = pd.wide_to_long(df, ["seats", "baseline", "percentage"], i=["time", "perc_counted_votes"], j="pparty", sep="_", suffix=".*")
    df = df.reset_index()
    # only keep parties with at least one seat
    seats_by_pparties = df.groupby("pparty")["seats"].sum()
    parties_with_seats = list(seats_by_pparties[seats_by_pparties > 0].index)
    return df[df["pparty"].isin(parties_with_seats)]



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
    df = df.groupby(["time", "perc_counted_votes", "blocks"]).sum().reset_index()
    # add center right block
    wide_df = df.pivot(index=["time", "perc_counted_votes", "baseline"], columns="blocks")
    for col in wide_df.columns.levels[0]:
        wide_df[(col, "Center-Right")] = wide_df.get((col, "Right"), 0) + wide_df.get((col, "Center"), 0)
    df = wide_df.stack(level=1).reset_index()
    return df


app.layout = html.Div(children=[
    html.H1(children='Madrid Elections 2021'),

    html.Div(
        id='title',
    ),

    dcc.Graph(
        id='graph-pparties'
    ),
    dcc.Graph(
        id='graph-blocks'
    ),
    dcc.Interval(
        id='interval-component',
        interval=1*10000, # in milliseconds
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
                  hover_data={"baseline": True, "pparty": False, "time": False, "percentage": True, "perc_counted_votes": True})
    # fig.update_layout(hovermode="x")
    return fig


@app.callback(
    Output('graph-blocks', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    df = get_df_by_blocks(state_path)
    fig = px.line(df, x="time", y="seats", color='blocks', hover_name="blocks",
                  hover_data={"baseline": True, "blocks": False, "time": False, "percentage": True, "perc_counted_votes": True})
    fig.update_layout(hovermode="x")
    return fig


@app.callback(
    Output('title', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_title(n):
    return (
            f"Minimal Dash application to follow the Election Results. Last updated on {get_last_update(state_path)}"
            f", with counted percentage of the votes at {get_counted_perc(state_path)}"
    )


if __name__ == '__main__':
    # df = get_df("fake.json")
    # df = get_df_by_blocks("fake.json")
    print("check in pycharm")
    app.run_server(debug=True)