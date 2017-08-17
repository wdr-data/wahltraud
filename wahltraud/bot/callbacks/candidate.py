import logging

from ..fb import send_buttons, button_postback, send_text, send_attachment
from ..data import by_uuid, find_candidates, random_candidate

logger = logging.getLogger(__name__)


def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    first_name = parameters.get('vorname')
    last_name = parameters.get('nachname')
    candidates = find_candidates(first_name, last_name)

    if len(candidates) > 1:
        send_buttons(sender_id, """
        Es gibt mehrere Kandidaten mit dem Namen {first_name} {last_name}. Von welcher Partei ist der gesuchte Kandidat?
        """.format(
            first_name=candidates[0]['first_name'],
            last_name=candidates[0]['last_name']
        ),
            [button_postback(candidate['party'],
                             {'payload_basics': candidate['uuid']})
             for candidate in candidates])
    else:
        show_basics(sender_id, candidates[0]['uuid'])

def payload_basics(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['payload_basics']

    show_basics(sender_id, candidate_uuid)

def show_basics(sender_id, candidate_uuid):
    candidate = by_uuid[candidate_uuid]
    district_uuid = candidate['district_uuid']
    if district_uuid:
        district = by_uuid[district_uuid]
        candidate_district = district['district'],
        state = district['state'],

    logger.debug('candidate_uuid: ' + str(candidate_uuid))

    if candidate['nrw'] is not None:
        profession = candidate['nrw']['profession']

        buttons = [
            button_postback("Anderer Kandidat", ['intro_candidate'])
        ]

        if not candidate['nrw']['pledges'] and candidate['nrw']['interests'] is None:
            buttons.insert(0, button_postback("Info Wahlkreis", {'show_district': district_uuid}))
        else:
            buttons.insert(0, button_postback("Mehr Info", {'more_infos_nrw': candidate['uuid']}))

        if candidate['nrw']['video'] is not None:
            video_url = candidate['nrw']['video']
            buttons.insert(0, button_postback("Interview", {'show_video': video_url}))
    else:
        profession = candidate['profession']
        if profession:
            profession = profession.replace('MdB', 'Mitglied des Bundestags')
        buttons = [
            button_postback("Info Wahlkreis", {'show_district': district_uuid}),
            button_postback("Anderer Kandidat", ['intro_candidate'])
        ]

    if 'img' in candidate:
        send_attachment(sender_id, candidate['img'], type='image')

    send_buttons(sender_id, """
{name}
Partei: {party}
Jahrgang: {age}

Wahlkreis: {dicstrict}
Landesliste: {state}
Listenplatz Nr.: {list_nr}
Beruf: {profession}
    """.format(
        name=' '.join(filter(bool, (candidate['degree'],
                                    candidate['first_name'],
                                    candidate['last_name']))),
        party=candidate['party'],
        age='-' if candidate['age'] is None else candidate['age'],
        dicstrict='-' if district_uuid is None else candidate_district,
        state='-' if district_uuid is None else state,
        list_nr='-' if candidate['list_nr'] is None else candidate['list_nr'],
        profession='-' if profession is None else profession
    ), buttons)

def more_infos_nrw(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['more_infos_nrw']
    candidate = by_uuid[candidate_uuid]

    if not candidate['nrw']['pledges']:
        pledges = None
    else:
        pledges = ['- ' + line for line in candidate['nrw']['pledges']]

    buttons = [
        button_postback("Info Wahlkreis", {'show_district': candidate['district_uuid']}),
        button_postback("Anderer Kandidat", ['intro_candidate'])
    ]

    if candidate['nrw']['video'] is not None:
        video_url = candidate['nrw']['video']
        buttons.insert(0, button_postback("Interview", {'show_video': video_url}))

    if candidate['nrw']['interests'] is None and pledges is not None:
        send_buttons(sender_id, """
Die Themen von {first_name} {last_name} in der kommenden Legislaturperiode sind ...
{pledges}
        """.format(
            first_name=candidate['first_name'],
            last_name=candidate['last_name'],
            pledges='\n'.join(pledges)), buttons)
    elif pledges is None and candidate['nrw']['interests']is not None:
        send_buttons(sender_id, """
Das Herz von {first_name} {last_name} schlägt für ...
{interests}
        """.format(
            first_name=candidate['first_name'],
            last_name=candidate['last_name'],
            interests=candidate['nrw']['interests']), buttons)
    else:
        send_buttons(sender_id, """
Die Themen von {first_name} {last_name} in der kommenden Legislaturperiode sind ...
{pledges}

{gender} Herz schlägt für ...
{interests}
        """.format(
            first_name=candidate['first_name'],
            last_name=candidate['last_name'],
            pledges='\n'.join(pledges),
            gender='Sein' if candidate['gender']=='male' else 'Ihr',
            interests=candidate['nrw']['interests']
        ), buttons)

def intro_candidate(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, "Du kannst mir direkt dem Namen eines Kandidaten als Nachricht schreiben.")

def candidate_check(event, **kwargs):
    reply = """
Du kannst Kandidaten nach Wahlkreis oder Partei suchen.
Alternativ kannst du auch direkt den Namen eines Kandidaten als Nachricht schreiben."""
    sender_id = event['sender']['id']

    send_buttons(sender_id, reply,
                 buttons=[button_postback('Wahlkreis', ['intro_district']),
                          button_postback('Partei', ['intro_lists']),
                          button_postback('Zufälliger Kandidat', {'payload_basics': random_candidate()['uuid']})])
