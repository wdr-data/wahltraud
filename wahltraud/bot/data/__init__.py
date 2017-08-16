
import json
import random
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

state_lists = defaultdict(lambda: defaultdict(list))

for candidate in candidate_list:
    by_first_name[candidate['first_name']].add(candidate['uuid'])
    by_last_name[candidate['last_name']].add(candidate['uuid'])

    if candidate.get('list_nr') is not None:
        state_lists[candidate['list_name']][candidate['party']].append(candidate)

    by_uuid[candidate['uuid']] = candidate

for district in district_list:
    for plz in district['plz']:
        by_plz[plz].add(district['uuid'])

    for city in district['cities']:
        by_city[city].add(district['uuid'])

    by_uuid[district['uuid']] = district

for state in state_lists.values():
    for party in state.keys():
        state[party] = list(sorted(state[party], key=operator.itemgetter('list_nr')))

def random_candidate():
    return random.choice(candidate_list)

def find_candidates(first_name, last_name):
    """Returns a list of candidates that have the given first and last name"""
    out = [by_uuid[uuid] for uuid in by_first_name[first_name] & by_last_name[last_name]]
    if out == []:
        out = by_last_name[last_name]
        if len(out) > len(by_first_name[first_name]):
            out = by_first_name[first_name]
    return out

MANIFESTO_DIR = Path(__file__).absolute().parent.parent/'output'

manifesto_file = MANIFESTO_DIR/'all.json'

all_words_list = json.load(open(str(manifesto_file)))['data']
all_words = {word['word']: word for word in all_words_list}

party_abbr = {
    'cdu': 'CDU',
    'spd': 'SPD',
    'fdp': 'FDP',
    'linke': 'DIE LINKE',
    'gruene': 'DIE GRÜNEN',
    'afd': 'AfD',
}

party_rev = {v: k for k, v in party_abbr.items()}

manifestos = dict()

for party in party_abbr:
    with open(str(MANIFESTO_DIR/('%s.txt' % party))) as fp:
        manifestos[party] = [line.strip() for line in fp.readlines()]