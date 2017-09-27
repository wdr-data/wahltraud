import logging
from ..fb import send_buttons, button_postback, button_url,  send_text, send_list, list_element, quick_reply
from ..data import by_party, party_list, party_candidates_grouped, by_uuid
from .candidate import show_basics

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
            "Die Top-7-Parteien sind in mindestens einem Landtag oder im Bundestag vertreten.",
            [
                button_postback("Top-7-Parteien", {'show_parties': 'etabliert'}),
                button_postback("mehr Parteien", {'show_parties': 'klein'})
                #,
                #button_postback("Zeige Alle", {'show_parties': 'alle'})
            ])

    else:
        show_party_options(event, {'show_party_options': party})


def top_candidates_apiai(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')

    top_cand_parties = ['CDU', 'SPD', 'AfD', 'GRÜNE', 'FDP', 'DIE LINKE', 'Die PARTEI']

    if not party:
        send_text(sender_id, 'Spitzenkandidaten...')
        show_parties(event, {'show_parties': 'top'})

    elif party in top_cand_parties:
        party_info = by_party[party]
        if len(party_info['top_candidates']) == 1:
            top_candidate = party_info['top_candidates'][0]
            # gender_candidate = by_uuid[top_candidate]
            show_basics(sender_id, top_candidate)
        else:
            show_top_candidates(event, {'show_top_candidates': party_info['top_candidates']})
    else:
        send_text(sender_id, 'Die Partei hat leider keinen Spitzenkandidaten aufgestellt.')


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
        'Ich kann dich wie folgt über die Partei "{party}" ({party_short}) informieren.'.format(
            party=party_info['name'], party_short=party_info['short']),
        buttons=buttons
    )




def show_top_candidates(event, payload, **kwargs):
    sender_id = event['sender']['id']
    top_candidates = payload['show_top_candidates']
    topa_uuid = top_candidates.pop(0)
    topb_uuid = top_candidates.pop(0)
    topa = by_uuid[topa_uuid]
    topb = by_uuid[topb_uuid]

    send_buttons(
        sender_id,
        "Die \"{party}\" hat folgende Spitzenkandidaten nominiert:".format(
            party=topa['party']),
        [button_postback(
            "{name}".format(
                name=' '.join(filter(bool, (topa['degree'],
                                    topa['first_name'],
                                    topa['last_name'])))),
            {'payload_basics': topa_uuid}
        ),
            button_postback(
                "{name}".format(
                    name=' '.join(filter(bool, (topb['degree'],
                                                topb['first_name'],
                                                topb['last_name'])))),
                    {'payload_basics': topb_uuid}
            )
        ]
    )


def show_party_candidates(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_party_candidates']
    party_info = by_party[party].copy()  # Make copy so we can .pop() without destroying data

    buttons = [button_postback(
                                "Landeslisten",
                                {'select_state': party}
                            ),
                            button_postback(
                                "ALLE (alphabetisch)",
                                {'show_list_all': party}
                            )
                    ]

    # choose spitzenkandidat wording
    if party_info['top_candidates'] is not None:
        if len(party_info['top_candidates']) == 2:
            buttons.insert(
                0,
                button_postback("Spitzenkandidaten",
                                {'show_top_candidates': party_info['top_candidates']}))
        else:
            top_candidate = party_info['top_candidates'].copy().pop(0)
            gender_candidate = by_uuid[top_candidate]
            if gender_candidate['gender'] == 'female':
                buttons.insert(
                    0,
                    button_postback("Spitzenkandidatin",
                                {'payload_basics': top_candidate}))

            else:
                buttons.insert(
                    0,
                    button_postback("Spitzenkandidat",
                                    {'payload_basics': top_candidate}))

    send_buttons(
        sender_id,
        "Wie magst du nach einem Kandidaten der Partei \"{party}\" suchen?".format(
            party=party_info['short']),
        buttons
    )


def show_list_all(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_list_all']
    offset = payload.get('offset', 0)
    group = payload.get('group')

    candidates_grouped = party_candidates_grouped[party]

    if len(candidates_grouped) > 1 and not group:
        options = [
            quick_reply(group, {'show_list_all': party, 'group': group})
            for group in sorted(candidates_grouped)
        ]
        send_text(
            sender_id,
            'Die Liste ist nach Nachnamen sortiert. Bitte wählen:',
            quick_replies=options
        )
        return

    elif len(candidates_grouped) == 1 and not group:
        candidates = next(iter(candidates_grouped.values()))
        group = next(iter(candidates_grouped.keys()))

        if len(candidates) == 1:
            send_text(sender_id, 'Die Partei "%s" hat nur einen Kandidaten:' % party)
            show_basics(sender_id, candidates[0]['uuid'])
            return

    elif group:
        candidates = candidates_grouped[group]

        if len(candidates) == 1:
            send_text(
                sender_id,
                'Die Partei "%s" hat nur einen Kandidaten von %s:' % (party, group)
            )
            show_basics(sender_id, candidates[0]['uuid'])
            options = [
                quick_reply(group, {'show_list_all': party, 'group': group})
                for group in sorted(candidates_grouped)
            ]
            send_text(
                sender_id,
                'Möchtest du noch mehr Kandidaten sehen?',
                quick_replies=options
            )
            return

    num_candidates = 4

    if len(candidates) - (offset + num_candidates) == 1:
        num_candidates = 3

    elements = [
        list_element(
            ' '.join(filter(bool, (candidate['degree'],
                                   candidate['first_name'],
                                   candidate['last_name']))),
            subtitle="%s, Jahrgang %s, %s" % (candidate['party'], candidate['age'] or 'unbekannt', 'gewählt' if candidate['member']== 1 else ''),
            buttons=[button_postback("Info", {'payload_basics': candidate['uuid']})],
            image_url=candidate.get('img') or None
        )
        for candidate in candidates[offset:offset + num_candidates]
    ]

    if len(candidates) - offset > num_candidates:
        button = button_postback("Mehr anzeigen",
                                 {'show_list_all': party,
                                  'group': group,
                                  'offset': offset + num_candidates})
    else:
        button = button_postback("Zurück", {'show_list_all': party})

    if not offset:
        send_text(
            sender_id,
            'Hier die alphabetische Liste der Partei "{party}" von {group}, '
            'sortiert nach Nachname.'.format(
                party=party, group=group)
        )

    send_list(sender_id, elements, button=button)


def show_electorial(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_electorial']
    party_info = by_party[party]

    skripts = ['CDU', 'SPD', 'AfD', 'GRÜNE', 'FDP', 'DIE LINKE']

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
            "Leider habe ich das Programm der Partei {party_short} (noch) nicht gelesen und kann keine Schlagwortsuche anbieten. ".format(
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
    elif category == 'etabliert':
        parties = ['CDU', 'CSU', 'SPD', 'DIE LINKE', 'GRÜNE', 'FDP', 'AfD' ]
    elif category =='top':
        parties =  ['CDU', 'CSU', 'SPD', 'DIE LINKE', 'GRÜNE', 'FDP', 'AfD', 'Die PARTEI' ]
    else:
        parties = [party['party'] for party in party_list if party['category'] == category]

    options = [
        quick_reply(p, {'show_party_options': p})
        for p in sorted(parties)
    ][offset:offset + 9]
    if category == 'etabliert':
        options = [
                      quick_reply(p, {'show_party_options': p})
                      for p in parties
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
        'Welche Partei interessiert dich?',
        quick_replies=options
    )