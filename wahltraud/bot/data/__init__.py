
import json
from pathlib import Path
from collections import defaultdict
import operator

DATA_DIR = Path(__file__).absolute().parent

candidate_list = json.load(open(str(DATA_DIR/'alle_kandidaten.json')))['list']
district_list = json.load(open(str(DATA_DIR/'wahlkreis_info.json')))['districts']

by_first_name = defaultdict(set)
by_last_name = defaultdict(set)
by_plz = defaultdict(set)
by_city = defaultdict(set)
by_uuid = dict()

state_lists = defaultdict(list)

for district in district_list:
    for plz in district['plz']:
        by_plz[plz].add(district['uuid'])

    for city in district['cities']:
        by_city[city].add(district['uuid'])

    by_uuid[district['uuid']] = district

for candidate in candidate_list:
    by_first_name[candidate['first_name']].add(candidate['uuid'])
    by_last_name[candidate['last_name']].add(candidate['uuid'])

    state_lists[by_uuid[candidate['district_uuid']]['state']].append(candidate)

    by_uuid[candidate['uuid']] = candidate

for state in state_lists.keys():
    state_lists[state] = list(sorted(state_lists[state], key=operator.itemgetter('list_nr')))


def find_candidates(first_name, last_name):
    """Returns a list of candidates that have the given first and last name"""
    return [by_uuid[uuid] for uuid in by_first_name[first_name] & by_last_name[last_name]]
