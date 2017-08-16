from ..fb import send_buttons, button_postback

def manifesto(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')
    topic = parameters.get('thema')

    if not party and not topic:
