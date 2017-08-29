import logging
from ..fb import send_buttons, button_postback, button_url,  send_text, send_list, list_element, quick_reply
from ..data import by_party, party_list

# Enable logging
logger = logging.getLogger(__name__)


def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')

    logger.debug('Infos zur Partei {party} angefordert.'.format(party=party))

    # no party
    if not party:
        send_buttons(
            sender_id,
            "Zur Wahl sind 42 Parteien vom Bundeswahlleiter zugelassen. "
            "Über welche magst du dich näher informieren?",
            [
                button_postback("Etablierte Parteien", {'show_parties': 'etabliert'}),
                button_postback("Kleine Parteien", {'show_parties': 'klein'})
                #,
                #button_postback("Zeige Alle", {'show_parties': 'alle'})
            ])

    else:
        show_party_options(event, {'show_party_options': party})


def show_party_options(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_party_options']
    party_info = by_party[party]

    buttons = [
        button_postback("Kandidaten", {'show_party_candidates': party}),
        button_url("Homepage", party_info['page'])
    ]

    # make decision process and handle in new payload function --> show_basics
    if party_info['skript']:
        buttons.insert(
            1,
            button_postback("Wahlprogramm", {'show_electorial': party})
        )

    send_buttons(
        sender_id,
        "Ich kann dich wie folgt über die Partei {party} ({party_short}) informieren.".format(
            party=party_info['name'], party_short=party_info['short']),
        buttons=buttons
    )


def show_party_candidates(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_party_candidates']
    party_info = by_party[party].copy()  # Make copy so we can .pop() without destroying data

    select_state_button = button_postback("Nach Bundesland", {'select_state': party})

    if party_info['top_candidates'] is not None:
        if len(party_info['top_candidates']) == 1:
            buttons = [
                button_postback(
                    "Spitzenkandidat",
                    {'payload_basics': party_info['top_candidates'].pop(0)}
                ),
                select_state_button,
                button_postback(
                    "ALLE (alphabetisch)",
                    {'show_list_all': party}
                )
            ]
        else:
            buttons = [
                button_postback(
                    "Spitzenkandidat A",
                    {'payload_basics': party_info['top_candidates'].pop(0)}
                ),
                button_postback(
                    "Spitzenkandidat B",
                    {'payload_basics': party_info['top_candidates'].pop(0)}
                ),
                select_state_button,
            ]
    else:
        buttons = [
            select_state_button,
            button_postback("ALLE (alphabetisch)", {'show_list_all': party}),
        ]

    send_buttons(
        sender_id,
        "Wie darf ich dir die Kandidaten der Partei \"{party}\" präsentieren?".format(
            party=party_info['short']),
        buttons
    )


def show_list_all(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_list_all']
    party_info = by_party[party]
    send_text(
        sender_id,
        "Hier sind bald alle 1000 Kandidaten der Partei \"{party}\" zu sehen.".format(
            party=party_info['short'])
    )


def show_electorial(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_electorial']
    party_info = by_party[party]

    skripts = ['CDU', 'SPD', 'AfD', 'DIE GRÜNEN', 'FDP', 'DIE LINKE']

    if party in skripts:
        send_buttons(
            sender_id,
            "Du kannst das Programm der Partei {party_short} nach Schlagworten durchsuchen "
            "oder über den Link das gesamte Programm ansehen.".format(
                party_short=party_info['short']
            ),
            [
                button_postback("Schlagwortsuche", ['manifesto_start']),
                button_url("Link zum Programm", party_info['skript']),
                button_postback("zurück", {'show_party_options': party})
            ]
        )
    else:
        send_buttons(
            sender_id,
            "Leider habe ich das Programm der Partei {party_short} nicht gelesen. ".format(
                party_short=party_info['short']
            ),
            [
                button_url("Link zum Programm", party_info['skript']),
                button_postback("zurück", {'show_party_options': party})
            ]
        )


def show_parties(event, payload, **kwargs):
    sender_id = event['sender']['id']
    category = payload['show_parties']
    offset = payload.get('offset', 0)

    if category == 'alle':
        parties = [party['party'] for party in party_list]
    else:
        parties = [party['party'] for party in party_list if party['category'] == category]

    options = [
        quick_reply(p, {'show_party_options': p})
        for p in sorted(parties)
    ][offset:offset + 9]

    if offset > 0:
        options.insert(
            0,
            quick_reply('⬅️', {'show_parties': category, 'offset': offset - 9})
        )

    if offset + 9 < len(parties):
        options.append(
            quick_reply('➡️', {'show_parties': category, 'offset': offset + 9})
        )

    send_text(
        sender_id,
        'Wähle die Partei aus, die dich interessiert:',
        quick_replies=options
    )