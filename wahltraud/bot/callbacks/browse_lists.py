import locale
import logging

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import state_lists

from .candidate import show_basics as show_candidate_basics
from .party import show_party_candidates

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')

# Enable logging
logger = logging.getLogger(__name__)

def intro_lists(event, **kwargs):
    sender_id = event['sender']['id']
    send_buttons(sender_id,
                 'Welches Bundesland interessiert dich?',
                 [
                     button_postback('NRW', {'select_party': 'Landesliste Nordrhein-Westfalen'}),
                     button_postback('Anderes Bundesland', ['select_state']),
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
            quick_reply(state[len('Landesliste '):],
                        {
                            'show_list': True,
                            'party': party,
                            'state': state,
                        })
            for state, parties in sorted(state_lists.items())
            if party in parties
        ]

    if not options:
        send_text(sender_id, 'Ich weiß von keinen Landeslisten der Partei "%s".' % party)
        return

    if not more and len(options) > 8:
        options = options[:8]
        options.append(
            quick_reply('➡️️', {
                'select_state': party,
                'more': True
            }))
    elif more:
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


def apiai(event, parameters, **kwargs):
    party = parameters.get('partei')
    state = parameters.get('bundesland')

    if not party and not state:
        intro_lists(event, **kwargs)
    elif party and not state:
        show_party_candidates(event, {'show_party_candidates': party})
        #select_state(event, {'select_state': party})
    elif state and not party:
        select_party(event, {'select_party': 'Landesliste %s' % state})
    elif party and state:
        show_list(event, {'party': party, 'state': 'Landesliste %s' % state})


def show_list(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['state']
    party = payload['party']
    offset = payload.get('offset', 0)

    logger.info('Landesliste anzeigen von Partei {party} im Bundesland {state}'.format(
        party=party, state=state))

    candidates = state_lists[state][party]
    if not candidates:
        send_text(sender_id, 'Die Partei %s hat keine %s' % (party, state))
        return

    if len(candidates) == 1:
        send_text(sender_id, 'Die %s der Partei %s hat nur einen Kandidaten:' % (state, party))
        show_candidate_basics(sender_id, candidates[0]['uuid'])
        return

    num_candidates = 4

    if len(candidates) - (offset + num_candidates) == 1:
        num_candidates = 3

    elements = [
        list_element(
            ' '.join(filter(bool, ('#%d -' % candidate['list_nr'],
                                   candidate['degree'],
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
                                 {'show_list': True,
                                  'party': party,
                                  'state': state,
                                  'offset': offset + num_candidates})
    else:
        button = button_postback("Andere Partei", {'select_party': state})

    if not offset:
        send_text(
            sender_id,
            'Hier die {list_name} der Partei {party}. '
            'Insgesamt sind {nr_of_candidates} Kandidaten aufgestellt.'.format(
                list_name=state, party=party, nr_of_candidates=candidates[-1]['list_nr'])
        )

    send_list(sender_id, elements, button=button)
