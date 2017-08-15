
import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).absolute().parent

candidate_list = json.load(open(str(DATA_DIR/'alle_kandidaten.json')))['list']
district_list = json.load(open(str(DATA_DIR/'wahlkreis_info.json')))['districts']

by_first_name = defaultdict(set)
by_last_name = defaultdict(set)
by_plz = defaultdict(set)
by_uuid = dict()

for candidate in candidate_list:
    by_first_name[candidate['first_name']].add(candidate['uuid'])
    by_last_name[candidate['last_name']].add(candidate['uuid'])
    by_uuid[candidate['uuid']] = candidate

for district in district_list:
    for plz in district['plz']:
        by_plz[plz].add(district['district_uuid'])

    by_uuid[district['district_uuid']] = district


def find_candidates(first_name, last_name):
    """Returns a list of candidates that have the given first and last name"""
    return [by_uuid[uuid] for uuid in by_first_name[first_name] & by_last_name[last_name]]