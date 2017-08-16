
def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')

    send_buttons(sender_id, """
Ich kann dich wie folgt über die  Partei {Partei} informieren. 
    """.format(
        party=party
    ),
                 [
                     button_postback("Landeslisten (Kandidaten)", {'more_infos': candidate['uuid']}),
                     button_postback("Wahlprogramm", ['intro_candidate']),
                     button_postback("Homepage", ['intro_candidate'])
                 ])