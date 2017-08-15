import logging

from ..fb import send_buttons, button_postback, send_text
from ..data import by_uuid, find_candidates

logger = logging.getLogger(__name__)

def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    first_name = parameters.get('vorname')
    last_name = parameters.get('nachname')
    candidates = dict()
    candidates = find_candidates(first_name, last_name)
    if len(candidates) > 1:
        send_buttons(sender_id, """
        Es gibt mehrere Kandidaten mit dem Namen {first_name} {last_name}. Von welcher Partei ist der gesuchte Kandidat?
        """.format(
            first_name=candidates[0]['first_name'],
            last_name=candidates[0]['last_name']
        ),
            [button_postback(candidate['party'],
                             {'show_basics': candidate['uuid']})
             for candidate in candidates])
    else:
        send_buttons(sender_id, """
        {first_name} {last_name}
        Partei: {party}
        Alter/ Jahrgang: {age}
        """.format(
            first_name=candidates[0]['first_name'],
            last_name=candidates[0]['last_name'],
            party=candidates[0]['party'],
            age=candidates[0]['age']
        ),
                     [
                         button_postback("Mehr Info", {'more_infos': candidates[0]['uuid']}),
                         button_postback("Anderer Kandidat", {'candidate_check': candidates[0]['uuid']})
                      ])

def show_basics(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['show_basics']
    candidate = by_uuid[candidate_uuid]

    logger.debug('candidate_uuid: ' + str(candidate_uuid))
    send_buttons(sender_id, """
    {first_name} {last_name}

Partei: {party}
Alter/ Jahrgang: {age}
    """.format(
        first_name=candidate['first_name'],
        last_name=candidate['last_name'],
        party=candidate['party'],
        age=candidate['age']
    ),
                 [
                     button_postback("Mehr Info", {'more_infos': candidate['uuid']}),
                     button_postback("Anderer Kandidat", {'candidate_check': candidate['uuid']})
                 ])

def more_infos(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['more_infos']
    candidate = by_uuid[candidate_uuid]
    district_uuid = candidate['district_uuid']
    district = by_uuid[district_uuid]

    if candidate['nrw'] is not None:
        profession=candidate['nrw']['profession']
        if candidate['nrw']['video'] is not None:
            video_url=candidate['nrw']['video']
            buttons = [
                        button_postback("Interview", {'show_video': video_url}),
                        button_postback("Mehr Info", {'more_infos_nrw': candidate['uuid']}),
                        button_postback("Anderer Kandidat", {'candidate_check': candidate['uuid']})
            ]
        else:
            buttons = [
                        button_postback("Mehr Info", {'more_infos_nrw': candidate['uuid']}),
                        button_postback("Anderer Kandidat", {'candidate_check': candidate['uuid']})
            ]
    else:
        profession=candidate['profession']
        if profession == 'MdB':
            profession = 'Mitglied des Bundestags'
        buttons = [
                    button_postback("Info Wahlkreis", {'show_district': district_uuid}),
                    button_postback("Anderer Kandidat", {'candidate_check': candidate['uuid']})
        ]

    send_buttons(sender_id, """
    Wahlkreis {dicstrict}

Landesliste {state}
Listenplatz Nr.: {list_nr}
Beruf: {profession}
    """.format(
        dicstrict=district['district'],
        state=district['state'],
        list_nr=candidate['list_nr'],
        profession=profession
    ),buttons)

def more_infos_nrw(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['more_infos']
    candidate = by_uuid[candidate_uuid]

    for line in candidate['nrw']['pledges']:
        pledges = '- ' + line

    if candidate['nrw']['video'] is not None:
        video_url=candidate['nrw']['video']
        buttons = [
                    button_postback("Interview", {'show_video': video_url}),
                    button_postback("Info Wahlkreis", {'show_district': candidate['district_uuid']}),
                    button_postback("Anderer Kandidat", {'candidate_check': candidate['uuid']})
        ]
    else:
        buttons = [
                    button_postback("Info Wahlkreis", {'show_district': candidate['district_uuid']}),
                    button_postback("Anderer Kandidat", {'candidate_check': candidate['uuid']})
        ]

    send_buttons(sender_id, """
    {pledges}

{interests}
    """.format(
        pledges=pledges,
        interests=candidate['nrw']['interests']
    ),buttons)

def candidate_check(event, **kwargs):
    reply = """
Du kannst Kandidaten nach Wahlkreis oder Partei suchen.
Alternativ kannst du auch direkt den Namen eines Kandidaten als Nachricht schreiben."""
    sender_id = event['sender']['id']

    send_buttons(sender_id, reply,
                 buttons=[button_postback('Wahlkreis', ['find_district']),
                          button_postback('Partei', ['party_list']),
                          button_postback('Zufälliger Kandidat', ['random_candidate'])])
