import logging
from ..fb import send_buttons, button_postback, button_url,  send_text, send_list, list_element, quick_reply
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
        send_buttons(sender_id, """
                    Zur Wahl sind 42 Parteien vom Bundeswahlleiter zugelassen. Über welche magst du dich näher informieren?
                    """,
                     [
                         button_postback("Etablierte Parteien", {'show_parties': 'etabliert'}),
                         button_postback("Kleine Parteien", {'show_parties': 'klein'}),
                         button_postback("Zeige Alle", {'show_parties': 'alle'})
                     ])

    else:
        # make decission process and handle in new payload function --> show_basics
        if not party_info['skript']:
            send_buttons(sender_id, """
                              Ich kann dich wie folgt über die  Partei {party} informieren.
                              """.format(
                                     party=party
                                         ),
                         [
                             button_postback("Kandidaten (Listen)", ['select_state']),
                             button_url("Homepage", party_info['page'])
                         ])
        else:
            send_buttons(sender_id, """
                Ich kann dich wie folgt über die  Partei {party} informieren.
                """.format(
                    party=party
                ),
                             [
                                 button_postback("Kandidaten (Listen)", ['select_state']),
                                 button_url("Wahlprogramm (PDF)",  party_info['skript']),
                                 button_url("Homepage",  party_info['page'])
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