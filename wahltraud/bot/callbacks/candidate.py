
from ..fb import send_buttons, button_postback, send_text


def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    first_name = parameters.get('vorname')
    last_name = parameters.get('nachname')
    send_text(
        sender_id,
        'Du möchtest etwas über {first_name} {last_name} erfahren?'.format(
            first_name=first_name, last_name=last_name))

def candidate_check(event, **kwargs):
    reply = """
    Du kannst Kandidaten nach Wahlkreis oder Partei suchen.
    Alternativ kannst du auch direkt den Namen eines Kandidaten als Nachricht schreiben."""
    sender_id = event['sender']['id']

    send_buttons(sender_id, reply,
                 buttons=[button_postback('Wahlkreis', ['find_district']),
                    button_postback('Partei', ['party_list']),
                    button_postback('Zufälliger Kandidat', ['random_candidate'])])

def find_district(event, **kwargs):
    reply = """
    Viele Wege führen zum Wahlkreis deiner Wahl. Am schnellsten geht es, indem du mir deine Postleitzahl schreibst."""
    sender_id = event['sender']['id']

    send_text(sender_id, reply)
