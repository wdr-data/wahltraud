import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element
from ..data import by_uuid, find_candidates, random_candidate

logger = logging.getLogger(__name__)


def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    first_name = parameters.get('vorname')
    last_name = parameters.get('nachname')
    candidates = find_candidates(first_name, last_name)

    if len(candidates) > 1:
        send_text(
            sender_id,
            "Deine Eingabe war wohl nicht eindeutig. Hier die Kandidaten, die in Frage kommen in alphabetischer Reihnefolge: "
        )
        show_search_candidate_list(
            event, candidates, first_name, last_name)

    elif len(candidates) == 1:
        show_basics(sender_id, candidates[0]['uuid'])
    else:
        send_text(
            sender_id,
            "Mhmm, leider habe ich niemanden mit diesem Namen gefunden. Achte, ob der Name richtig geschrieben ist."
        )


def search_candidate_list(event, payload, **kwargs):
    first_name = payload['first_name']
    last_name = payload['last_name']
    offset = payload['offset']
    candidates = find_candidates(first_name, last_name)

    show_search_candidate_list(
        event, candidates, first_name, last_name, offset)


def show_search_candidate_list(event, candidates, first_name, last_name, offset=0):
    sender_id = event['sender']['id']
    candidates = list(sorted(candidates,
                             key=lambda c: (c['last_name'], c['first_name'], c['uuid'])))
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
                                 {'search_candidate_list': True,
                                  'first_name': first_name,
                                  'last_name': last_name,
                                  'offset': offset + num_candidates})
    else:
        button = None

    send_list(sender_id, elements, button=button)


def payload_basics(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['payload_basics']

    show_basics(sender_id, candidate_uuid)

def show_basics(sender_id, candidate_uuid):
    candidate = by_uuid[candidate_uuid]
    district_uuid = candidate['district_uuid']
    if district_uuid:
        district = by_uuid[district_uuid]
        candidate_district = district['district']
        candidate_district_id = district['district_id']
        state = district['state']

    logger.info('Kandidatencheck {name} von Partei {party}'.format(
        name=' '.join(filter(bool, (candidate['degree'],
                                    candidate['first_name'],
                                    candidate['last_name']))),
        party=candidate['party']))

    if candidate['nrw'] is not None:
        profession = candidate['nrw']['profession']

        buttons = [
            button_postback("Weitere Kandidaten", ['intro_candidate'])
        ]

        if not candidate['nrw']['pledges'] and candidate['nrw']['interests'] is None:
            buttons.insert(0, button_postback("Info Wahlkreis " + candidate_district_id, {'show_district': district_uuid}))
        else:
            buttons.insert(0, button_postback("Mehr Info", {'more_infos_nrw': candidate['uuid']}))

        if candidate['nrw']['video'] is not None:
            video_url = candidate['nrw']['video']
            buttons.insert(0, button_postback("Interview", {'show_video': video_url}))
        else:
            buttons.insert(0, button_postback("Interview", {'no_video_to_show': candidate['uuid']}))

        if candidate['nrw']['img'] is not None:
            send_attachment(sender_id, candidate['nrw']['img'], type='image')
        elif candidate['img'] is not None:
            send_attachment(sender_id, candidate['img'], type='image')
    else:
        profession = candidate['profession']
        if profession:
            profession = profession.replace('MdB', 'Mitglied des Bundestags')
        buttons = [
            button_postback("Info Wahlkreis " + candidate_district_id, {'show_district': district_uuid}),
            button_postback("Weitere Kandidaten", ['intro_candidate'])
        ]

        if candidate['img'] is not None:
            send_attachment(sender_id, candidate['img'], type='image')

    send_buttons(sender_id, """
Ein paar Fakten über {name}:
Partei: {party}
Jahrgang: {age}
Beruf: {profession}

Wahlkreis: {dicstrict}
Listenplatz Nr.: {list_nr}
Landesliste {state}
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


def no_video_to_show(event,payload,**kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['no_video_to_show']
    candidate = by_uuid[candidate_uuid]
    district_uuid = candidate['district_uuid']
    district = by_uuid[district_uuid]
    candidate_district_id = district['district_id']

    logger.info('Kandidatencheck - keine video von {name} von Partei {party}'.format(
        name=' '.join(filter(bool, (candidate['degree'],
                                    candidate['first_name'],
                                    candidate['last_name']))),
        party=candidate['party']))

    buttons = [
        button_postback("Info Wahlkreis " + candidate_district_id, {'show_district': candidate['district_uuid']}),
        button_postback("Weitere Kandidaten", ['intro_candidate'])
    ]

    send_buttons(sender_id, """
    Leider gibt es von {first_name} {last_name} (noch) kein Interview. 
    
    {zusatz_info}
            """.format(
                    first_name=candidate['first_name'],
                    last_name=candidate['last_name'],
                    zusatz_info = candidate['nrw']["zusatz"]
                    ), buttons)


def more_infos_nrw(event, payload, **kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = payload['more_infos_nrw']
    candidate = by_uuid[candidate_uuid]
    district_uuid = candidate['district_uuid']
    district = by_uuid[district_uuid]
    candidate_district_id = district['district_id']

    logger.info('Kandidatencheck - mehr Infos zu {name} von Partei {party}'.format(
        name=' '.join(filter(bool, (candidate['degree'],
                                    candidate['first_name'],
                                    candidate['last_name']))),
        party=candidate['party']))

    if not candidate['nrw']['pledges']:
        pledges = None
    else:
        pledges = ['- ' + line for line in candidate['nrw']['pledges']]

    buttons = [
        button_postback("Info Wahlkreis " + candidate_district_id, {'show_district': district_uuid}),
        button_postback("Weitere Kandidaten", ['intro_candidate'])
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
            gender='Ihr' if candidate['gender']=='female' else 'Sein',
            interests=candidate['nrw']['interests']
        ), buttons)

def show_video(event, payload, **kwargs):
    sender_id = event['sender']['id']
    url = payload['show_video']

    logger.info('Kandidatencheck Video: {url}'.format(url=url))

    send_attachment(sender_id, url, type='video')

def intro_candidate(event, **kwargs):
    reply = """
    Über 2800 Kandidaten stehen in 299 Wahlkreisen zur Wahl. 
    """
    sender_id = event['sender']['id']
    #send_text(sender_id, "Du kannst mir direkt dem Namen eines Kandidaten als Nachricht schreiben.")
    send_buttons(sender_id, reply,
                 buttons=[button_postback('Wahlkreis (Direktkandidat)', ['intro_district']),
                          button_postback('Partei (Landeslisten)', ['intro_lists']),
                          button_postback('Zufalls-KandidatIn', {'payload_basics': random_candidate()['uuid']})])


def candidate_check(event, **kwargs):
    reply = """
Du kannst dir die zur Wahl stehenden Kandidaten nach Wahlkreis oder Partei anzeigen lassen. Ich habe zu allen Kandidaten ein paar Infos. 
Oder schick mir einfach den Namen eines bestimmten Kandidaten! """
    sender_id = event['sender']['id']

    send_buttons(sender_id, reply,
                 buttons=[button_postback('Wahlkreis (Direktkandidat)', ['intro_district']),
                          button_postback('Partei (Landeslisten)', ['intro_lists']),
                          button_postback('Zufalls-KandidatIn', {'payload_basics': random_candidate()['uuid']})])
