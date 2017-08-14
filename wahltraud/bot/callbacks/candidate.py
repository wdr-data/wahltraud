
from ..fb import send_buttons, button_postback, send_text


def basics(event, **kwargs):
    sender_id = event['sender']['id']
    first_name = kwargs['parameters'].get('vorname')
    last_name = kwargs['parameters'].get('nachname')
    send_text(sender_id, 'Du möchtest etwas über %s %s erfahren?' % (first_name, last_name))
