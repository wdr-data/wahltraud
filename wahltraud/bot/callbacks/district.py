import locale
import operator
import logging
import random
import pandas as pd

from django.conf import settings


from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply, send_attachment, button_web_url
from ..data import by_uuid, by_plz, by_city, get_election13_dict, get_structural_data, result_by_district_id

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')

# Enable logging
logger = logging.getLogger(__name__)

def intro_district(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, "Schick mir eine Postleitzahl und ich sage dir, wer in dem Wahlkreis kandidiert!")


def find_district(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    plz = parameters.get('plz')
    city = parameters.get('orte')

    if not plz and not city:
        reply = """
Wenn du mir einen Ort oder deine PLZ nennst, bekommst du von mir Infos zum Wahlkreis."""

        send_text(sender_id, reply)

    else:
        if plz:
            district_uuids = by_plz.get(plz)
        else:
            district_uuids = by_city.get(city)

        if not district_uuids:
            if plz:
                send_text(sender_id, "Diese PLZ sagt mir leider nichts...")
            else:
                send_text(sender_id, "Tut mir Leid, diesen Ort kenne ich nicht...")

        elif len(district_uuids) == 1:
            send_district(sender_id, next(iter(district_uuids)))
            #district = by_uuid[next(iter(district_uuids))]
            #show_district(sender_id, {"show_district": district['uuid']})

        elif len(district_uuids) < 4:
            send_buttons(sender_id,
                         'In deinem PLZ-Gebiet gibt es wohl mehrere Wahlkreise!',
                         [button_postback(district['district'],
                                          {'show_district': district['uuid']})
                          for district in
                          [by_uuid[uuid] for uuid in district_uuids]]
                         )

        elif len(district_uuids) < 12:
            send_text(sender_id,
                      'Hier alle Wahlkreise die ich finden konnte. Gib mir eine PLZ und die Liste wird kleiner!'
                      ,
                      [quick_reply(district['district'],
                                   {'show_district': district['uuid']})
                       for district in
                       [by_uuid[uuid] for uuid in district_uuids]]
                      )
        else:
            send_text(sender_id,
                      "{city} hat {n} Wahlkreise! So viele kann ich leider nicht anzeigen. "
                      "Bitte sende mir stattdessen deine PLZ.".format(
                          city=city,
                          n=len(district_uuids)))


def send_district(sender_id, district_uuid):
    event = {'sender': {'id': sender_id}}
    show_district(event, {'show_district': district_uuid})
    """
    send_buttons(sender_id,
                 'Ok. Der Wahlkreis deiner Wahl ist {district}'.format(
                     district=by_uuid[district_uuid]['district']),
                 [button_postback("Zeige Wahlkreis-Info",
                                  {'show_district': district_uuid})])
    """

def show_district(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_district']
    district = by_uuid[district_uuid]

    logger.info('Wahlkreisinfo: {district} - {number}'.format(
        district=district['district'], number=district['district_id']))

    send_attachment(
        sender_id,
        settings.SITE_URL + '/static/bot/wkmaps/wk'+str(district['district_id'])+'.png'
    )


    send_buttons(sender_id, """
Wahlkreis {number},  "{name}", liegt in {state}. Hier stehen {nr_of_candidates} Direktkandidaten zur Wahl, davon sind {total_female} Frauen.
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
                     button_postback("Wahlkreis in Zahlen", {'show_structural_data': district_uuid}),
                    #  button_postback("Ergebnis Wahl '13", {'show_13': district_uuid})
                     button_postback("Ergebnis 2017", {'result_17': district_uuid})
                     #button_postback("Anderer Wahlkreis", ['intro_district']),
                 ])

def novi(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['novi']
    district = by_uuid[district_uuid]

    novi_wk = str(district['district_id']).zfill(3)

    send_buttons(sender_id, """
Am Sonntag ist es soweit - du kannst bis 18 Uhr in deinem Wahllokal deine Stimme abgeben. Und dann? Dann heißt es warten...
Wenn du informiert werden möchtest, sobald dein Wahlkreis {number},  "{name}", ausgezählt ist, dann wende dich an meinen Bot-Kollegen "Novi". Er schickt dir eine Nachricht mit dem entsprechenden Ergebnis.
Ich leite deinen Wahlkreis gerne an "Novi" weiter. Klicke dazu einfach auf "Zu Novi".
""".format(
        number=district['district_id'],
        name=district['district']),
        [
            button_web_url("Zu Novi", "https://m.me/getnovibot?ref=WK" + novi_wk)
        ])

def show_13(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_13']
    show_all = payload.get('show_all', False)

    district = by_uuid[district_uuid]
    election_13 = district['election_13'].copy()
    election_13_all = get_election13_dict()

    beteiligung = election_13.pop('wahlbeteiligung')


    logger.info('Wahl 2013 zu Wahlkreis: {district}'.format(
        district=district['district']))

    results = '\n'.join(
        [
            locale.format_string('%s: %.1f%%  (%.1f%%)', (party, result * 100, election_13_all[party]*100))
            for party, result
            in sorted(election_13.items(), key=operator.itemgetter(1), reverse=True)
            if (show_all and result>0)  or result > 0.0499
        ]
    )

    if show_all:
        send_buttons(
            sender_id,
            "Alle Parteien im Überblick:"
            "\n\n{results}".format(
                results=results),
            [
                button_postback("Info Wahlkreis " + district['district_id'], {'show_structural_data': district_uuid}),
                button_postback("Anderer Wahlkreis", ['intro_district']),
            ]
        )

    else:
        send_buttons(
            sender_id,
            "Bei der Bundestagswahl 2013 haben diese Parteien im Wahlkreis \"{district}\" "
            "mehr als 5% der Zweitstimmen erhalten:"
            "\n\n{results}\n\nDie Wahlbeteiligung betrug {beteiligung}%  ({beteiligung_all}%). ".format(
                results=results,
                beteiligung_all = locale.format('%.1f', election_13_all['wahlbeteiligung']*100 ),
                district=district['district'],
                beteiligung=locale.format('%.1f', beteiligung * 100)),
            [
                button_postback("Alle anzeigen", {'show_13': district_uuid, 'show_all': True}),
                button_postback("Info Wahlkreis " + district['district_id'], {'show_structural_data': district_uuid}),
                button_postback("Anderer Wahlkreis", ['intro_district']),
            ]
        )

def result_17(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['result_17']
    district = by_uuid[district_uuid]

    election_17 = result_by_district_id[district['district_id']]
    first_vote = election_17['first17']
    second_vote = election_17['second17']

    first_vote_results = '\n'.join(
        [
            locale.format_string('%s: %.1f%%', (party, result * 100))
            for party, result
            in sorted(first_vote.items(), key=operator.itemgetter(1), reverse=True)[:3]
        ]
    )
    second_vote_results = '\n'.join(
        [
            locale.format_string('%s: %.1f%%', (party, result * 100))
            for party, result
            in sorted(second_vote.items(), key=operator.itemgetter(1), reverse=True)
            if result > 0.0499
        ]
    )

    candidates = list(sorted((by_uuid[uuid] for uuid in district['candidates']),
                             key=operator.itemgetter('last_name')))
    logger.info('Kandidat der Partei {party} mit Direktmandat im Wahlkreis {district} ist: {candidate}'.format(
        party = first_vote_results[0].split(":", 1),
        district=district['district'],
        candidate = candidates[0]))
    winner_candidate = ' '.join(
        [
            locale.format_string('%s (%s)', (' '.join(candidate['degree'],
                                            candidate['first_name'],
                                            candidate['middle_name'],
                                            candidate['pre_last_name'],
                                            candidate['last_name']),
                                            party))
            for party in by_uuid(candidates)
            #if party = first_vote_results
        ]
    )

    url = 'https://media.data.wdr.de:8080/static/bot/result_grafics/second_distric' + district['district_id'] + '.jpg'
    send_attachment(sender_id, url, type='image')

    send_buttons(
            sender_id,
            "Bei der Bundestagswahl 2017 hat durch die Erststimme der Wähler {candidate} das Direktmandat im Wahlkreis \"{district}\" gewonnen."
            "\nFolgende Parteien haben sich auf die ersten drei Plätze gekämpft:"
            "\n\n{results} ".format(
                candidate = winner_candidte,
                district=district['district'],
                results = first_vote_results),
            [
                button_postback("Info Direktkandidat", {'payload_basics': random_candidate['uuid']}),
                button_postback("Ergebnis Erststimme", {'result_first_vote': district_uuid}),
                button_postback("Ergebnis Zweitstimme", {'result_second_vote': district_uuid}),
            ]
        )

def result_first_vote(event, payload, **kwargs):
    sender_id = event['sender']['id']

    send_text(
        sender_id,
        "Es folgt eine Auflistung aller Ergebnisse der Erststimme."
    )

def result_second_vote(event, payload, **kwargs):
    sender_id = event['sender']['id']

    send_text(
        sender_id,
        "Es folgt eine Auflistung aller Ergebnisse der Zweitstimme."
    )

def show_candidates(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_candidates']
    offset = int(payload.get('offset', 0))
    district = by_uuid[district_uuid]
    candidates = list(sorted((by_uuid[uuid] for uuid in district['candidates']),
                             key=operator.itemgetter('last_name')))
    logger.info('Kandidatenliste zu Wahlkreis: {district}'.format(
        district=district['district']))

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

    if offset ==0:
        send_text(sender_id,
                  'Hier die Liste der Direktkandidaten im Wahlkreis \"{district}\" in alphabetischer Reihenfolge:'
                  .format(
                    district = district['district']
                        )
                  )
    send_list(sender_id, elements, button=button)


def show_structural_data(event,payload,**kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_structural_data']
    district = by_uuid[district_uuid]

    data = get_structural_data(district['district_id'])

    logger.info('Wahlkreisinfo Struckturdaten: {district} - {number}'.format(
        district=district['district'], number=district['district_id']))

    send_buttons(sender_id, """
    Die folgenden Strukturdaten des Wahlkreis "{name}" stellt der Bundeswahlleiter zur Verfügung:

Gesamt Bevölkerung: {population}
Wahlberechtigt: ca. {voters}

Die Alterverteilung ist wie folgt:
    unter 18: {u18}%
    18-24: {a1824}%
    25-34: {a2534}%
    35-59: {a3559}%
    60-75: {a6075}%
    75 und mehr: {a75}%

(Stand 31.12.2015)

Arbeitslosenquote (März '17): {unemployed}%
Bevölkerung pro km²: {perm2}
    """.format(
        u18 = locale.format('%.1f',data['u18']),
        a1824=locale.format('%.1f',data['a1824']),
        a2534=locale.format('%.1f',data['a2534']),
        a3559=locale.format('%.1f',data['a3559']),
        a6075=locale.format('%.1f',data['a6075']),
        a75=locale.format('%.1f',data['a75']),
        perm2=locale.format('%.1f',data['perm2']),
        voters=locale.format('%.0f',data['voters_tot']),
        unemployed=locale.format('%.1f',data['unemployed']),
        population=locale.format('%.0f',data['population']),
        name=district['district'],

    ),
                 [
                     button_postback("Kandidaten", {'show_candidates': district_uuid}),
                     button_postback("Ergebnis per Push", {'novi': district_uuid}),
                     button_postback("Ergebnis Wahl '13", {'show_13': district_uuid})
                    #  button_postback("Anderer Wahlkreis", ['intro_district']),
                 ])
