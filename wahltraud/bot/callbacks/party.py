import logging
from ..fb import send_buttons, button_postback, button_url, send_text
from ..data import by_party

# Enable logging
logger = logging.getLogger(__name__)

def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')
    party_info = by_party[party]

    logger.info('Infos zur Partei {party} angefordert.'.format(party=party))

    # no party
    if not party:
        send_text(
            sender_id,
            "Es treten 42 Parteien zur Wahl an"
        )

    else:

        if not party_info['skript']:
            send_buttons(sender_id, """
            Ich kann dich wie folgt über die  Partei {party} informieren.
            """.format(
                party=party
            ),
                         [
                             button_postback("Kandidaten (Listen)", ['select_state']),
                             button_url("Wahlprogramm",  party_info['skript']),
                             button_url("Homepage",  party_info['page'])
                         ])
        else:
            send_buttons(sender_id, """
                    Ich kann dich wie folgt über die  Partei {party} informieren.
                    """.format(
                party=party
            ),
                         [
                             button_postback("Kandidaten (Listen)", ['select_state']),
                             button_url("Homepage",  party_info['page'])
                         ])


