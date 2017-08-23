import locale
import operator

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import by_uuid, by_plz, by_city

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def intro_district(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, "Lass mich schauen, wer in deinem Wahlkreis zur Wahl steht. "
                         "Schreib mir doch einfach deine PLZ, und ich schaue nach.")


def find_district(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    plz = parameters.get('plz')
    city = parameters.get('orte')

    if not plz and not city:
        reply = """
Viele Wege führen zum Wahlkreis deiner Wahl. Am schnellsten geht es, indem du mir
deine Postleitzahl schreibst."""

        send_text(sender_id, reply)

    else:
        if plz:
            district_uuids = by_plz.get(plz)
        else:
            district_uuids = by_city.get(city)

        if not district_uuids:
            if plz:
                send_text(sender_id, "Diese PLZ sagt mir nichts...")
            else:
                send_text(sender_id, "Tut mir Leid, diesen Ort kenne ich nicht...")

        elif len(district_uuids) == 1:
            send_district(sender_id, next(iter(district_uuids)))

        elif len(district_uuids) < 4:
            send_buttons(sender_id,
                         'Welchen Wahlkreis meinst du?',
                         [button_postback(district['district'],
                                          {'show_district': district['uuid']})
                          for district in
                          [by_uuid[uuid] for uuid in district_uuids]]
                         )

        elif len(district_uuids) < 12:
            send_text(sender_id,
                      'Bitte wähle einen der folgenden Wahlkreise. '
                      'Alternativ kannst du mir auch deine PLZ senden.',
                      [quick_reply(district['district'],
                                   {'show_district': district['uuid']})
                       for district in
                       [by_uuid[uuid] for uuid in district_uuids]]
                      )
        else:
            send_text(sender_id,
                      "{city} hat {n} Wahlkreise. So viele kann ich leider nicht anzeigen. "
                      "Bitte sende mir stattdessen deine PLZ.".format(
                          city=city,
                          n=len(district_uuids)))


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
Der Wahlkreis {number},  "{name}", liegt in {state}. Hier stehen {nr_of_candidates} Kandidaten zur Wahl, davon sind {total_female} Frauen. 
Das Durchschnittsalter der Kandidaten beträgt {avg_age} Jahre.
""".format(
        number=district['district_id'],
        name=district['district'],
        state=district['state'],
        nr_of_candidates=len(district['candidates']),
        total_female = district['meta']['females_total'],
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
    show_all = payload.get('show_all', False)

    district = by_uuid[district_uuid]
    election_13 = district['election_13'].copy()

    beteiligung = election_13.pop('wahlbeteiligung')

    results = '\n'.join(
        [
            locale.format_string('%s: %.1f%%', (party, result * 100))
            for party, result
            in sorted(election_13.items(), key=operator.itemgetter(1), reverse=True)
            if show_all or result > 0.05
        ]
    )

    if show_all:
        send_buttons(
            sender_id,
            "Alle Parteien im Überblick:"
            "\n\n{results}".format(
                results=results),
            [
                button_postback("Anderer Wahlkreis", ['intro_district']),
            ]
        )

    else:
        send_buttons(
            sender_id,
            "Bei der Bundestagswahl 2013 haben diese Parteien im Wahlkreis \"{district}\" "
            "mehr als 5% der Zweitstimmen erhalten:"
            "\n\n{results}\n\nDie Wahlbeteiligung betrug {beteiligung}%.".format(
                results=results,
                district=district['district'],
                beteiligung=locale.format('%.1f', beteiligung * 100)),
            [
                button_postback("Alle anzeigen", {'show_13': district_uuid, 'show_all': True}),
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

    if len(candidates) - (offset + num_candidates) == 1:
        num_candidates = 3

    elements = [
        list_element(
            ' '.join(filter(bool, (candidate['degree'],
                                   candidate['first_name'],
                                   candidate['last_name']))),
            subtitle="%s, Jahrgang %s" % (candidate['party'], candidate['age'] or 'unbekannt'),
            buttons=[button_postback("Info", {'payload_basics': candidate['uuid']})],
            image_url=candidate.get('img') or None
        )
        for candidate in candidates[offset:offset + num_candidates]
    ]

    if len(candidates) - offset > num_candidates:
        button = button_postback("Mehr anzeigen",
                                 {'show_candidates': district_uuid,
                                  'offset': offset + num_candidates})
    else:
        button = button_postback("Anderer Wahlkreis", ['intro_district'])


    send_list(sender_id, elements, button=button)
