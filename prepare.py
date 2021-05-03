import xml.etree.ElementTree as ET
import requests
import datetime
import os
import json
import time
from collections import defaultdict
from const import storage_filename, madrid_elecciones_2019, datetime_format

def extract(e, keys, get_text=True, to_num=True):
    new_e = e
    if isinstance(keys, str):
        keys = [keys]
    for key in keys:
        new_e = new_e.find(key)
    if get_text:
        text = new_e.text
        if to_num:
            return float(text)
        return new_e.text
    return new_e


def get_election_state(url):
    elections_state = {}
    text = requests.get(url).text
    root = ET.fromstring(text)

    # general info
    elections_state["retrieval_time"] = datetime.datetime.utcnow().strftime(datetime_format)
    elections_state["total_seats"] = extract(root, ["num_a_elegir"])
    elections_state["perc_counted_votes"] = extract(root, ["porciento_escrutado"])
    ballots = extract(root, "votos", get_text=False)
    elections_state["turnout"] = extract(ballots, ["contabilizados", "porcentaje"])
    elections_state["perc_null_ballots"] = extract(ballots, ["nulos", "porcentaje"])
    elections_state["perc_blank_ballots"] = extract(ballots, ["blancos", "porcentaje"])

    results = {}
    for partido_xml in root.iter("partido"):
        results[extract(partido_xml, "nombre", to_num=False)] = {
            "ballots": extract(partido_xml, "votos_numero"),
            "perc_ballots": extract(partido_xml, "votos_porciento"),
            "seats": extract(partido_xml, "electos")
        }
    elections_state["results"] = results

    return elections_state


def add_2019(out_filename=storage_filename):
    '''This function adds 2019 to the state iff storage JSON file has not been created'''
    if os.path.exists(out_filename):
        print("state file already exists, doing nothing")
        return
    state = {}
    state_2019 = get_election_state(madrid_elecciones_2019)
    state["2019"] = [state_2019]
    with open(out_filename, "w") as fd:
        json.dump(state, fd)


def add_state(url, year, state_path=storage_filename, check_state=True):
    '''Tries to retrieve JSON from state_path. If it doesn't exist, work with empty dictionary. If check_state is True,
    then will check if new state perc_counted_votes is larger than max perc_counted_votes'''
    # tries to load state
    state_history = None
    try:
        with open(state_path) as fd:
            state_history = defaultdict(list, json.load(fd))
    except FileNotFoundError:
        print("state not found, assuming which is empty")
        state_history = defaultdict(list)
    new_state = get_election_state(url)
    if check_state:
        max_perc_counted_votes = (
            max([state["perc_counted_votes"] for state in state_history[year]]) if state_history.get(year)
            else None
        )
        if max_perc_counted_votes is None or max_perc_counted_votes < new_state["perc_counted_votes"]:
            print("adding current state of the elections to state object...")
            state_history[year].append(new_state)
        else:
            print("same state of the election, not updating document")
            return
    else:
        print("adding current state of the elections to state object...")
        state_history[year].append(new_state)
    with open(state_path, "w") as fd:
        json.dump(state_history, fd)


if __name__ == '__main__':
    add_2019("fake.json")
    add_2019()
    print("playing in pycharm")