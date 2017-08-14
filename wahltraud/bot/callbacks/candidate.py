
from ..fb import send_buttons, button_postback, send_text


def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    first_name = parameters.get('vorname')
    last_name = parameters.get('nachname')
    send_text(
        sender_id,
        'Du möchtest etwas über {first_name} {last_name} erfahren?'.format(
            first_name=first_name, last_name=last_name))
