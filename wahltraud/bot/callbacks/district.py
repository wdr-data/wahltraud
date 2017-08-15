import locale
import operator

from ..fb import send_buttons, button_postback, send_text, send_list, list_element
from ..data import by_uuid, by_plz

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def intro_district(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, "Lass mich schauen, wer in deinem Wahlkreis zur Wahl steht. "
                         "Schreib mir doch einfach deine PLZ, und ich schaue nach.")


def find_district(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    plz = parameters['plz']

    if not plz:
        reply = """
Viele Wege führen zum Wahlkreis deiner Wahl. Am schnellsten geht es, indem du mir 
deine Postleitzahl schreibst."""

        send_text(sender_id, reply)

    else:
        district_uuids = by_plz.get(plz)

        if not district_uuids:
            send_text(sender_id, "Diese PLZ sagt mir nichts...")

        elif len(district_uuids) == 1:
            send_district(sender_id, district_uuids.pop())

        else:
            send_buttons(sender_id,
                         'Welchen Wahlkreis meinst du?',
                         [button_postback(district['district'],
                                          {'show_district': district['uuid']})
                          for district in
                          [by_uuid[uuid] for uuid in district_uuids]]
                         )


def send_district(sender_id, district_uuid):
    send_buttons(sender_id,
                 'Ok. Der Wahlkreis deiner Wahl ist {district}'.format(
                     district=by_uuid[district_uuid]['district']),
                 [button_postback("Zeige Wahlkreis-Info",
                                  {'show_district': district_uuid})])


def show_district(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_district']
    district = by_uuid[district_uuid]

    send_buttons(sender_id, """
Der Wahlkreis "{name}" hat die Nummer {number} und liegt in {state}. Es treten {nr_of_candidates} Kandidaten an, deren Durchschnittsalter {avg_age} Jahre beträgt. 
""".format(
        number=district['district_id'],
        name=district['district'],
        state=district['state'],
        nr_of_candidates=len(district['candidates']),
        avg_age=locale.format('%.1f', 2017.7 - district['meta']['avg_age'])
    ),
                 [
                     button_postback("Kandidaten", {'show_candidates': district_uuid}),
                     button_postback("Bundestagswahl 2013", {'show_13': district_uuid}),
                     button_postback("Anderer Wahlkreis", ['intro_district']),
                 ])


def show_13(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_13']
    district = by_uuid[district_uuid]
    election_13 = district['election_13'].copy()

    beteiligung = election_13.pop('wahlbeteiligung')

    results = '\n'.join(
        [
            locale.format_string('%s: %.1f%%', (party, result * 100))
            for party, result
            in sorted(election_13.items(), key=operator.itemgetter(1), reverse=True)
            if result >= 0.05
        ]
    )

    send_buttons(
        sender_id,
        "Bei der Bundestagswahl 2013 haben diese Parteien mehr als 5% der Zweitstimmen erhalten:"
        "\n\n{results}\n\nDie Wahlbeteiligung betrug {beteiligung}%.".format(
            results=results,
            beteiligung=locale.format('%.1f', beteiligung * 100)),
        [
            button_postback("Anderer Wahlkreis", ['intro_district']),
        ]
    )


def show_candidates(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_candidates']
    offset = int(payload.get('offset', 0))
    district = by_uuid[district_uuid]
    candidates = list(sorted((by_uuid[uuid] for uuid in district['candidates']),
                             key=operator.itemgetter('last_name')))
    num_candidates = 4

    if len(candidates) - (offset + num_candidates) < 2:
        num_candidates = 3

    elements = [
        list_element(
            "%s %s" % (candidate['first_name'], candidate['last_name']),
            subtitle="%s" % (candidate['party']),
            buttons=[button_postback("Info", {'show_basics': candidate['uuid']})]
        )
        for candidate in candidates[offset:offset + num_candidates]
    ]

    button = None
    if len(candidates) - offset > num_candidates:
        button = button_postback("Mehr anzeigen",
                                 {'show_candidates': district_uuid,
                                  'offset': offset + num_candidates})

    send_list(sender_id, elements, button=button)
