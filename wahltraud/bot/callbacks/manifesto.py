import locale

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import all_words, party_abbr

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def search_word_apiai(event, parameters, **kwargs):
    word = parameters.get('thema')
    party = parameters.get('partei')

    if not party:
        search_word(event, word)


def search_word_payload(event, payload, **kwargs):
    word = payload.get('search_word')
    offset = payload.get('offset', 0)
    search_word(event, word, offset)


def search_word(event, word, offset=0):
    sender_id = event['sender']['id']
    stat = all_words.get(word)

    if not stat:
        send_text(sender_id, 'Hmmm... dieses Wort erkenne ich nicht.')
        return

    segs = stat['segments']

    if len(segs) == 1:
        party, seg = next(iter(segs.items()))
        send_buttons(
            sender_id,
            'Dieses Wort kommt nur im Wahlprogramm der Partei "{party}" vor, und zwar {n} mal '
            '({share}% aller Wörter).'.format(
                party=party_abbr[party],
                n=seg['count'],
                share=locale.format('%.2f', seg['share'] * 100),
            ),
            [button_postback("Zeige Satz", {'show_sentence': word, 'party': party})]
        )
        return

    num_words = 4

    if len(segs) - (offset + num_words) == 1:
        num_words = 3

    elements = [
        list_element(
            party_abbr[party],
            subtitle="Anzahl: %d (%s%%)" % (seg['count'],
                                            locale.format('%.2f', seg['share'] * 100)),
            buttons=[button_postback("Zeige Satz", {'show_sentence': word, 'party': party})],
        )
        for party, seg in sorted(segs.items())
    ][offset:offset + num_words]

    if len(segs) - offset > num_words:
        button = button_postback("Mehr anzeigen",
                                 {'search_word': word,
                                  'offset': offset + num_words})
    else:
        button = button_postback("Neues Wort", ['random_word'])

    if not offset:
        send_text(
            sender_id,
            'Wusstest Du, dass das Wort "{word}" insgesamt {n} mal in den Wahlprogrammen aller '
            'Parteien vorkommt?'.format(
                word=word,
                n=stat['count']
            ))

    send_list(sender_id, elements, button=button)
