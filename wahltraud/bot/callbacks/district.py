import locale
import operator
import logging
import random
import pandas as pd

from django.conf import settings


from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply, send_attachment, button_web_url
from ..data import by_uuid, by_plz, by_city, election13_dict, get_structural_data, result_by_district_id

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')

# Enable logging
logger = logging.getLogger(__name__)

def intro_district(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, "Schick mir eine Postleitzahl und ich sage dir, wer in dem Wahlkreis gewonnen hat!")


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
                                          {'result_17': district['uuid']})
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
    # show_district(event, {'show_district': district_uuid})
    result_17(event, {'result_17': district_uuid})
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
                    #  button_postback("Ergebnis per Push", {'novi': district_uuid}),
                    #  button_postback("Ergebnis Wahl '13", {'show_13': district_uuid})
                     button_postback("Ergebnis 2017", {'result_17': district_uuid}),
                     #button_postback("Anderer Wahlkreis", ['intro_district']),
                 ])

def novi(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['novi']
    district = by_uuid[district_uuid]

    novi_wk = str(district['district_id']).zfill(3)

    send_buttons(sender_id, """
Die Wahllokale sind geschlossen und die ersten Prognosen sind raus. Frag mich einfach nach dem Ergebnis.

Wenn du informiert werden möchtest, sobald dein Wahlkreis {number},  "{name}", ausgezählt ist, dann wende dich an meinen Bot-Kollegen "Novi".
Ich leite deinen Wahlkreis gerne an "Novi" weiter.

Morgen früh ab 7 Uhr hab ich dann auch dein Wahlkreis-Ergebnis".
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

    beteiligung = election_13.pop('wahlbeteiligung')


    logger.info('Wahl 2013 zu Wahlkreis: {district}'.format(
        district=district['district']))

    results = '\n'.join(
        [
            locale.format_string('%s: %.1f%%  (%.1f%%)', (party, result * 100, election13_dict[party] * 100))
            for party, result
            in sorted(election_13.items(), key=operator.itemgetter(1), reverse=True)
            if (show_all and result > 0) or result > 0.0499
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
                beteiligung_all=locale.format('%.1f', election13_dict['wahlbeteiligung'] * 100),
                district=district['district'],
                beteiligung=locale.format('%.1f', beteiligung * 100)),
            [
                button_postback("Alle anzeigen", {'show_13': district_uuid, 'show_all': True}),
                button_postback("Info Wahlkreis " + district['district_id'], {'show_structural_data': district_uuid}),
                button_postback("Anderer Wahlkreis", ['intro_district']),
            ]
        )

def result_nation_17(event, parameters, **kwargs):
    sender_id = event['sender']['id']

    url = 'https://media.data.wdr.de:8080/static/bot/result_grafics/second_distric999.jpg'
    send_attachment(sender_id, url, type='image')

    send_buttons(
            sender_id,
            "Hier die Ergebnisse der #BTW17 aus dem gesamten Bundesgebiet."
            "\nDie Grafik zeigt dir das vorläufige Ergebnis der Zweitstimmen-Auszählung. Alle Zahlen erhältst du bei \"Ergebnis Zweitstimme\"."
            "\n\nWenn du wissen möchtest, wie die Wahl in deinem Wahlkreis ausgegangen ist, "
            "dann schicke mir einfach deine Postleitzahl oder den Namen deiner Stadt.",
        [
            button_postback("Ergebnis Zweitstimme", {'result_second_vote': '999', 'nation': True}),
            #button_postback("Ergebnis NRW", {'result_state_17': 'Nordrhein-Westfalen'}),
            button_postback("Ergebnis Bundesländer", ['select_state_result']),
            button_postback("Aktuelle Info", ['gruss']),
        ]
    )

def result_state_17(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['result_state_17']

    state_mapping = {"Schleswig-Holstein": 901,
                    "Mecklenburg-Vorpommern": 913,
                    "Hamburg": 902,
                    "Niedersachsen": 903,
                    "Bremen" :904,
                    "Brandenburg": 912,
                    "Sachsen-Anhalt":915,
                    "Berlin": 911,
                    "Nordrhein-Westfalen": 905,
                    "Sachsen": 914,
                    "Hessen":906,
                    "Thüringen": 916,
                    "Rheinland-Pfalz": 907,
                    "Bayern":909,
                    "Baden-Württemberg": 908,
                    "Saarland": 910
                }

    url = 'https://media.data.wdr.de:8080/static/bot/result_grafics/second_distric'+str(state_mapping[state])+'.jpg'
    send_attachment(sender_id, url, type='image')

    send_buttons(
            sender_id,
            "Hier die Ergebnisse der #BTW17 aus {state}."
            "\nDie Grafik zeigt dir das vorläufige Ergebnis der Zweitstimmen-Auszählung. Alle Zahlen erhältst du bei \"Ergebnis Zweitstimme\"."
            "\n\nWenn du wissen möchtest, wie die Wahl in deinem Wahlkreis ausgegangen ist, "
            "dann schicke mir einfach deine Postleitzahl oder den Namen deiner Stadt.".format(
                state = state
            ),
        [
            button_postback("Ergebnis Zweitstimme", {'result_second_vote': str(state_mapping[state]), 'nation': True, 'state_id': state_mapping[state]}),
            button_postback("Ergebnis Bundesländer", ['select_state_result']),
            button_postback("Aktuelle Info", ['gruss']),
        ]
    )


def select_state_result(event, payload, **kwargs):
    sender_id = event['sender']['id']
    more = 'more' in payload

    party = 'schnaps'

    if not isinstance(payload, dict):
        payload = {pl: None for pl in payload}

    states = [
        "Schleswig-Holstein",
        "Mecklenburg-Vorpommern",
        "Hamburg",
        "Niedersachsen",
        "Bremen",
        "Brandenburg",
        "Sachsen-Anhalt",
        "Berlin",
        "Nordrhein-Westfalen",
        "Sachsen",
        "Hessen",
        "Thüringen",
        "Rheinland-Pfalz",
        "Bayern",
        "Baden-Württemberg",
        "Saarland"
    ]



    options = [
        quick_reply(state,
                    {
                        'result_state_17':state
                    })
        for state in sorted(states)
    ]



    if not more and len(options) > 8:
        options = options[:8]
        options.append(
            quick_reply('➡️️', {
                'select_state_result': party,
                'more': True
            }))
    elif more:
        options = options[8:]
        options.insert(0, quick_reply('⬅️️️', {'select_state_result': party}))

    send_text(sender_id, 'Wähle dein Bundesland', quick_replies=options)


def result_17(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['result_17']
    district = by_uuid[district_uuid]

    election_17 = result_by_district_id[district['district_id']]
    first_vote = election_17['first17']
    # second_vote = election_17['second17']

    first_vote_results = '\n'.join(
        [
            locale.format_string('(%s): %.1f%%', (party, result * 100))
            for party, result
            in sorted(first_vote.items(), key=operator.itemgetter(1), reverse=True)[:3]
        ]
    )
    candidates = list(sorted((by_uuid[uuid] for uuid in district['candidates']),
                             key=operator.itemgetter('last_name')))

    winner_candidate = dict()
    second_candidate = dict()
    third_candidate = dict()
    for candidate in candidates:
        if candidate['party'] in first_vote_results.split('\n')[0].split(':')[0]:
            winner_candidate = candidate
        if candidate['party'] in first_vote_results.split('\n')[1].split(':')[0]:
            second_candidate = candidate
        if candidate['party'] in first_vote_results.split('\n')[2].split(':')[0]:
            third_candidate = candidate

    logger.info('Kandidat der Partei {party} mit Direktmandat im Wahlkreis {district} ist: {candidate}'.format(
        party = first_vote_results.split(':')[0],
        district=district['district'],
        candidate = winner_candidate))

    url = 'https://media.data.wdr.de:8080/static/bot/result_grafics/second_distric' + district['district_id'] + '.jpg'
    send_attachment(sender_id, url, type='image')

    send_buttons(
            sender_id,
            "Hier die Ergebnisse der #BTW17 aus dem Wahlkreis \"{district}\"."
            "\nOben siehst du das vorläufige Ergebnis der Zweitstimmen-Auszählung. Die meisten Erststimmen haben folgende Kandidaten erhalten:"
            "\n{first}\n{second}\n{third}\n\n"
            "Damit bekommt {candidate} das Direktmandat in diesem Wahlkreis und wird Mitglied des 19. Bundestages.".format(
                candidate=' '.join(filter(bool, (winner_candidate['degree'],
                                            winner_candidate['first_name'],
                                            winner_candidate['middle_name'],
                                            winner_candidate['pre_last_name'],
                                            winner_candidate['last_name']))),
                district=district['district'],
                first = ' '.join(filter(bool, (winner_candidate['first_name'],
                                winner_candidate['last_name'],
                                first_vote_results.split('\n')[0]))),
                second = ' '.join(filter(bool, (second_candidate['first_name'],
                                second_candidate['last_name'],
                                first_vote_results.split('\n')[1]))),
                third = ' '.join(filter(bool, (third_candidate['first_name'],
                                third_candidate['last_name'],
                                first_vote_results.split('\n')[2])))),
            [
                button_postback("Info Direktkandidat", {'payload_basics': winner_candidate['uuid']}),
                button_postback("Ergebnis Erststimme", {'result_first_vote': district_uuid, 'winner_candidate': winner_candidate['uuid']}),
                button_postback("Ergebnis Zweitstimme", {'result_second_vote': district_uuid, 'winner_candidate': winner_candidate['uuid']}),
            ]
        )

def result_first_vote(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['result_first_vote']
    district = by_uuid[district_uuid]

    winner_candidate = payload['winner_candidate']
    election_17 = result_by_district_id[district['district_id']]
    first_vote = election_17['first17']

    party_candidate = {
        c['party']: ' '.join(
            filter(bool,
                   (c['first_name'], c['middle_name'], c['pre_last_name'], c['last_name'])))
        for c in
        (by_uuid[uuid] for uuid in district['candidates'])
    }

    first_vote_results = '\n'.join(
        [
            locale.format_string('%s (%s): %.1f%%',
                                 (party_candidate.get(party, '-'), party, result * 100))
            for party, result
            in sorted(first_vote.items(), key=operator.itemgetter(1), reverse=True)
        ]
    )

    send_buttons(
            sender_id,
            "Hier das vorläufige Ergebnis der Erststimmen-Auszählung im Wahlkreis {district}:"
            "\n\n{result}".format(
                district = district['district'],
                result = first_vote_results
            ),
            [
                button_postback("Info Wahlkreis " + district['district_id'], {'show_district': district_uuid}),
                button_postback("Info Direktkandidat", {'payload_basics': winner_candidate}),
                button_postback("Ergebnis Zweitstimme", {'result_second_vote': district_uuid, 'winner_candidate': winner_candidate}),
            ]
        )

def result_second_vote(event, payload, **kwargs):
    sender_id = event['sender']['id']
    winner_candidate = payload.get('winner_candidate')
    district_uuid = payload.get('result_second_vote')
    nation = payload.get('nation', False)

    if nation:
        election_17 = result_by_district_id[district_uuid]
        second_vote = election_17['second17']
        second_vote_13 = election_17['second13']

        second_vote_results = '\n'.join(
            [
                locale.format_string('%s: %.1f%% (%.1f%%)', (party, result * 100, second_vote_13.get(party, 0) * 100))
                for party, result
                in sorted(second_vote.items(), key=operator.itemgetter(1), reverse=True)
            ]
        )

        send_buttons(
            sender_id,
            "Hier das vorläufige Ergebnis der Zweitstimmen-Auszählung (in Klammern dahinter das Ergebnis der Partei bei der BTW 2013):"
            "\n\n{result}".format(
                result = second_vote_results
            ),
            [
                button_postback("Ergebnis Bundesländer", ['select_state_result']),
                button_postback("Wahlkreis-Ergebnis", ['intro_district']),
            ]
        )
    else:
        district = by_uuid[district_uuid]

        election_17 = result_by_district_id[district['district_id']]
        second_vote = election_17['second17']
        second_vote_13 = election_17['second13']

        second_vote_results = '\n'.join(
            [
                locale.format_string('%s: %.1f%% (%.1f%%)',
                                     (party, result * 100, second_vote_13.get(party, 0) * 100))
                for party, result
                in sorted(second_vote.items(), key=operator.itemgetter(1), reverse=True)
                # if result > 0.0499
            ]
        )

        send_buttons(
            sender_id,
            "Hier das vorläufige Ergebnis der Zweitstimmen-Auszählung im Wahlkreis {district} "
            "(in Klammern dahinter das Ergebnis der Partei bei der BTW 2013):"
            "\n\n{result}".format(
                district = district['district'],
                result = second_vote_results
            ),
            [
                button_postback("Info Wahlkreis " + district['district_id'], {'show_district': district_uuid}),
                button_postback("Info Direktkandidat", {'payload_basics': winner_candidate}),
                button_postback("Ergebnis Erststimme", {'result_first_vote': district_uuid, 'winner_candidate': winner_candidate}),
            ]
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
                      button_postback("Ergebnis 2017", {'result_17': district_uuid}),
                    #  button_postback("Ergebnis per Push", {'novi': district_uuid}),
                     button_postback("Ergebnis Wahl '13", {'show_13': district_uuid})
                    #  button_postback("Anderer Wahlkreis", ['intro_district']),
                 ])
