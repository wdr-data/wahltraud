from ..fb import send_buttons

def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')

    send_buttons(sender_id, """
Ich kann dich wie folgt über die  Partei {party} informieren.
    """.format(
        party=party
    ),
                 [
                     button_postback("Landeslisten (Kandidaten)", ['select_state']),
                     button_postback("Wahlprogramm", ['intro_candidate']),
                     button_postback("Homepage", ['intro_candidate'])
                 ])
