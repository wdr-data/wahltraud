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
        show_basics(candidates[0]['uuid'])
        # send_buttons(sender_id, """
        # {first_name} {last_name}
        # Partei: {party}
        # Alter/ Jahrgang: {age}
        # """.format(
        #     first_name=candidates[0]['first_name'],
        #     last_name=candidates[0]['last_name'],
        #     party=candidates[0]['party'],
        #     age=candidates[0]['age']
        # ),
        #              [
        #                  button_postback("Mehr Info", {'more_infos': candidates[0]['uuid']}),
        #                  button_postback("Anderer Kandidat", {'candidate_check': candidates[0]['uuid']})
        #              ])

def show_basics(event, parameters, *kwargs):
    sender_id = event['sender']['id']
    candidate_uuid = parameters.get('uuid')
    candidate = by_uuid(candidate_uuid)

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


def candidate_check(event, **kwargs):
    reply = """
Du kannst Kandidaten nach Wahlkreis oder Partei suchen.
Alternativ kannst du auch direkt den Namen eines Kandidaten als Nachricht schreiben."""
    sender_id = event['sender']['id']

    send_buttons(sender_id, reply,
                 buttons=[button_postback('Wahlkreis', ['find_district']),
                          button_postback('Partei', ['party_list']),
                          button_postback('Zufälliger Kandidat', ['random_candidate'])])
