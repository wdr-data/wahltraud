from ..fb import send_buttons, button_postback

def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')
    party_info = by_party[party]
    if 'skript' in party_info:
        send_buttons(sender_id, """
        Ich kann dich wie folgt über die  Partei {party} informieren.
        """.format(
            party=party
        ),
                     [
                         button_postback("Kandidaten (Listen)", ['select_state']),
                         button_postback("Wahlprogramm", {'show_link': party_info['skript']}),
                         button_postback("Homepage",  {'show_link': party_info['page']})
                     ])
    else:
        send_buttons(sender_id, """
                Ich kann dich wie folgt über die  Partei {party} informieren.
                """.format(
            party=party
        ),
                     [
                         button_postback("Kandidaten (Listen)", ['select_state']),
                         button_postback("Homepage", {'show_link': party_info['page']})
                     ])
