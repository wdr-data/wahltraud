
import json
import random
import logging
from pathlib import Path
from collections import defaultdict
import operator

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).absolute().parent

party_list = json.load(open(str(DATA_DIR/'parteien_info.json')))['list']
candidate_list = json.load(open(str(DATA_DIR/'alle_kandidaten.json')))['list']
district_list = json.load(open(str(DATA_DIR/'wahlkreis_info.json')))['districts']

by_first_name = defaultdict(set)
by_last_name = defaultdict(set)
by_plz = defaultdict(set)
by_city = defaultdict(set)
by_uuid = dict()
by_party = defaultdict(set)

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

for party in party_list:
    by_party[party['party']] = party

for state in state_lists.values():
    for party in state.keys():
        state[party] = list(sorted(state[party], key=operator.itemgetter('list_nr')))

def random_candidate():
    return random.choice(candidate_list)

def find_party(party_wanted):
    return by_party.get(party_wanted)

def find_candidates(first_name, last_name):
    """Returns a list of candidates that have the given first and last name"""
    out = by_first_name[first_name] & by_last_name[last_name]
    if not out:
        last_name_matches = by_last_name[last_name]
        first_name_matches = by_first_name[first_name]

        if 0 < len(last_name_matches) < len(first_name_matches) or not first_name_matches:
            out = last_name_matches
        else:
            out = first_name_matches

        if len(out) != 1 and (len(last_name_matches) + len(first_name_matches)) <= 4:
            out = last_name_matches & first_name_matches

    return [by_uuid[uuid] for uuid in out]

MANIFESTO_DIR = Path(__file__).absolute().parent.parent/'output'

manifesto_file = MANIFESTO_DIR/'all.json'

all_words_list = json.load(open(str(manifesto_file)))['data']
all_words = {word['word']: word for word in all_words_list}
random_words_list = [
    word['word']
    for word in all_words_list
    if word['word'][0].isupper() and word['count'] > 10
]

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
