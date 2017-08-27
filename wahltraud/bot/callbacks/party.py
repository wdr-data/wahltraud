import logging
from ..fb import send_buttons, button_postback, button_url,  send_text, send_list, list_element, quick_reply
from ..data import by_party

# Enable logging
logger = logging.getLogger(__name__)

def basics(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    party = parameters.get('partei')


    logger.info('Infos zur Partei {party} angefordert.'.format(party=party))

    # no party
    if not party:
        send_buttons(sender_id, """
                    Zur Wahl sind 42 Parteien vom Bundeswahlleiter zugelassen. Über welche magst du dich näher informieren?
                    """,
                     [
                         button_postback("Etablierte Parteien", {'show_parties': 'etabliert'}),
                         button_postback("Kleine Parteien", {'show_parties': 'klein'}),
                         button_postback("Zeige Alle", {'show_parties': 'alle'})
                     ])

    else:
        show_party_options(event, {'show_party_options': party})


def show_party_options(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_party_options']
    party_info = by_party[party]


    # make decission process and handle in new payload function --> show_basics
    if not party_info['skript']:
        send_buttons(sender_id, """
                                  Ich kann dich wie folgt über die Partei {party} ({party_short}) informieren.
                                  """.format(
            party=party_info['name'], party_short=party_info['short']
        ),
                     [
                         button_postback("Kandidaten", {'show_party_candidates': party}),
                         button_url("Homepage", party_info['page'])
                     ])
    else:
        send_buttons(sender_id, """
                   Ich kann dich wie folgt über die Partei {party} ({party_short}) informieren.
                                  """.format(
            party=party_info['name'], party_short=party_info['short']
        ),
                     [
                         button_postback("Kandidaten", {'show_party_candidates': party}),
                         button_postback("Wahlprogramm", {'show_electorial': party}),
                         button_url("Homepage", party_info['page'])
                     ])




def show_party_candidates(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_party_candidates']
    party_info = by_party[party]

    buttons =  [
                button_postback("nach Bundesland", {'select_state': party}),
                ]

    if party_info['top_candidates'] is not None:
        if len(party_info['top_candidates']) == 1:
            buttons.insert(0, button_postback("Spitzenkandidat", {'payload_basics': party_info['top_candidates'].pop(0)}))
            buttons.insert(2, button_postback("ALLE (alphabetisch)", {'show_list_all': party}))
        else:
            buttons.insert(0, button_postback("Spitzenkandidat B", {'payload_basics': party_info['top_candidates'].pop(0)}))
            buttons.insert(0, button_postback("Spitzenkandidat A", {'payload_basics': party_info['top_candidates'].pop(0)}))
    else:

        buttons.insert(2, button_postback("ALLE (alphabetisch)", {'show_list_all': party}))



    send_buttons(sender_id, """
                    Wie darf ich dir die Kandidaten der Partei {party} präsentieren?
                """.format(
                    party = party_info['short']
                ), buttons)


def show_list_all(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_list_all']
    party_info = by_party[party]
    send_text(sender_id, "Hier sind bald alle 1000 Kandidaten der Partei {party} zu sehen. Viel Freude".format(
        party = party_info['short']
    ))




def show_electorial(event, payload, **kwargs):
    sender_id = event['sender']['id']
    party = payload['show_electorial']
    party_info = by_party[party]

    skripts = ['CDU', 'SPD', 'AfD', 'DIE GRÜNEN', 'FDP', 'DIE LINKE']

    if party in skripts:
        send_buttons(sender_id, """
                       Du kannst das Programm der Partei {party_short} nach Schlagworten durchsuchen oder dir direkt zum Programm gelangen.
                   """.format(
            party_short=party_info['short']
        ),
                     [
                         button_postback("Schlagwortsuche", ['manifesto_start']),
                         button_url("Wahlprogramm (PDF)", party_info['skript']),
                         button_postback("zurück", {'show_party_options': party})
                     ])
    else:
        send_buttons(sender_id, """
                         Leider habe ich das Programm der Partei {party_short} nicht gelesen. 
                     """.format(
            party_short=party_info['short']
        ),
                     [
                         button_url("Wahlprogramm (PDF)", party_info['skript']),
                         button_postback("zurück", {'show_party_options': party})
                     ])




def show_parties(event, payload, **kwargs):
    sender_id = event['sender']['id']
    kind = payload['show_parties']


    #if not isinstance(payload, dict):
    #    payload = {pl: None for pl in payload}


    if kind == 'etabliert':
        send_text(sender_id,'Hier sind bald die etablierte Parteien aufgelistet (Bundestag und im Landtag vertretende)')
        '''
        options = [
            quick_reply(sl[len('Landesliste '):], {'select_party': sl})
            for sl in sorted(state_lists)
        ] 
        '''
    elif kind == 'klein':
        send_text(sender_id,'Hier findest du bald die kleinen Parteien')
        '''
        
        options = [
            quick_reply(sl[len('Landesliste '):],
                        {
                            'show_list': True,
                            'party': party,
                            'state': sl,
                        })
            for sl in sorted(state_lists)
        ]
        '''
    else:
        send_text(sender_id, 'Hier sind bald alle Parteien alphabetisch aufgelistet')
    '''
        
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
    '''