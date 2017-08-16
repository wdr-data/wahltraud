from ..fb import send_buttons, button_postback

def manifesto(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')
    topic = parameters.get('thema')

    if not party and not topic:
        reply = """
Was steht eigentlich in so einem Wahlprogramm?
Kaum ein Wähler liest sich ein Wahlprogramm durch. Ich biete Dir an dieser Stelle einen Einblick in die einzelnen Programme und zwar zu dem Thema, welches dich interessiert."""

        send_buttons(sender_id, reply,
                    buttons=[button_postback('Zufälliges Wort', ['random_topic']),
                             button_postback('Zufälliger Satz', ['random_topic_party']),
                             button_postback('Wie funktionierts?', ['about_manifesto'])])

def about_manifesto(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['about_manifesto']

    manifesto_info(sender_id, quick_reply, state)

def manifesto_info(sender_id, quick_reply, state='intro'):
    if state == 'intro':
        button = quick_reply('mehr', '', image_url=None)
        send_text(sender_id, "Du kannst jederzeit ein Wort eintippen und ich schaue nach in welchen Wahlprogrammen es vorkommt, z.B. Steuern.", quick_reply)
