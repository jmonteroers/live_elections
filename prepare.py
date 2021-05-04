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
    response = requests.get(url)
    if response.status_code != 200:
        print("Couldn't access elPais website")
        return
    text = response.text
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


def add_baseline(out_filename=storage_filename, baseline_year="2019", baseline_url=madrid_elecciones_2019):
    '''This function adds 2019 to the state iff storage JSON file has not been created'''
    state = None
    if os.path.exists(out_filename):
        print("state file already exists, loading")
        with open(out_filename) as fd:
            state = json.load(fd)
    state = state or {}
    if baseline_year not in state:
        baseline_state = get_election_state(baseline_url)
        state[baseline_year] = [baseline_state]
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
    if not new_state:
        return
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


def initialise_document(state_path, url, year, baseline_url, baseline_year):
    if os.path.exists(state_path):
       print("Can't initialise state history document, as it's already initialised")
       return
    state_history = {}
    # add baseline
    state_history[baseline_year] = [get_election_state(baseline_url)]
    # add initial snapshot of current elections
    state_history[year] = [get_election_state(url)]
    with open(state_path) as fd:
        json.dump(state_history, fd)


if __name__ == '__main__':
    add_baseline("fake.json")
    add_baseline()
    print("playing in pycharm")