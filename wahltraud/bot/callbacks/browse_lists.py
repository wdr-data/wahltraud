import locale
import operator

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import by_uuid, by_plz, by_city, state_lists

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def intro_lists(event, **kwargs):
    sender_id = event['sender']['id']
    send_buttons(sender_id,
                 'Welches Bundesland interessiert dich?',
                 [
                     button_postback('NRW', {'select_party': 'Landesliste Nordrhein-Westfalen'}),
                     button_postback('Ein anderes Bundesland', ['select_state']),
                 ])


def select_state(event, payload, **kwargs):
    sender_id = event['sender']['id']
    more = 'more' in payload

    if not isinstance(payload, dict):
        payload = {pl: None for pl in payload}

    party = payload['select_state']

    if not party:
        options = [
            quick_reply(sl[len('Landesliste '):], {'select_party': sl})
            for sl in sorted(state_lists)
        ]
    else:
        options = [
            quick_reply(sl[len('Landesliste '):],
                        {
                            'show_list': True,
                            'party': party,
                            'state': sl,
                        })
            for sl in sorted(state_lists)
        ]

    if not more:
        options = options[:8]
        options.append(
            quick_reply('➡️️', {
                'select_state': party,
                'more': True
            }))
    else:
        options = options[8:]
        options.insert(0, quick_reply('⬅️️️', {'select_state': party}))

    send_text(sender_id, 'Wähle dein Bundesland', quick_replies=options)


def select_party(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['select_party']
    offset = payload.get('offset', 0)

    parties = state_lists[state]

    options = [
        quick_reply(p, {
            'show_list': True,
            'party': p,
            'state': state,
        })
        for p in sorted(parties)
    ][offset:offset + 9]

    if offset > 0:
        options.insert(
            0,
            quick_reply('⬅️', {'select_party': state, 'offset': offset - 9})
        )

    if offset + 9 < len(parties):
        options.append(
            quick_reply('➡️', {'select_party': state, 'offset': offset + 9})
        )

    send_text(
        sender_id,
        'Wähle die Partei, deren Liste du anschauen möchtest:',
        quick_replies=options
    )


def show_list(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['state']
    party = payload['party']
    offset = payload.get('offset', 0)

    candidates = state_lists[state][party]

    num_candidates = 4

    if len(candidates) - (offset + num_candidates) == 1:
        num_candidates = 3

    elements = [
        list_element(
            ' '.join(filter(bool, (candidate['degree'],
                                   candidate['first_name'],
                                   candidate['last_name']))),
            subtitle="#%d, %s, Jahrgang %s" % (candidate['list_nr'],
                                               candidate['party'],
                                               candidate['age'] or 'unbekannt'),
            buttons=[button_postback("Info", {'payload_basics': candidate['uuid']})],
            image_url=candidate.get('img') or None
        )
        for candidate in candidates[offset:offset + num_candidates]
    ]

    if len(candidates) - offset > num_candidates:
        button = button_postback("Mehr anzeigen",
                                 {'show_list': True,
                                  'party': party,
                                  'state': state,
                                  'offset': offset + num_candidates})
    else:
        button = button_postback("Andere Partei", {'select_party': state})

    if not offset:
        send_text(
            sender_id,
            'Hier die {list_name} der Partei {party}'.format(list_name=state, party=party)
        )

    send_list(sender_id, elements, button=button)
