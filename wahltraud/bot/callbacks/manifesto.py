import locale
import random
from re import findall

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import all_words, party_abbr, manifestos

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def show_word_apiai(event, parameters, **kwargs):
    word = parameters.get('thema')
    party = parameters.get('partei')

    if not party:
        show_word(event, word, 0, **kwargs)
    else:
        show_sentence(event, word, party, **kwargs)


def show_word_payload(event, payload, **kwargs):
    word = payload.get('show_word')
    offset = payload.get('offset', 0)
    show_word(event, word, offset, **kwargs)


def show_sentence_payload(event, payload, **kwargs):
    word = payload.get('show_sentence')
    party = payload.get('party')
    show_sentence(event, word, party, **kwargs)


def show_word(event, word, offset, **kwargs):
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
                                 {'show_word': word,
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


def show_sentence(event, word, party, **kwargs):
    sender_id = event['sender']['id']
    occurences = all_words[word]['segments'][party]['occurence']
    occurence = random.choice(occurences)
    paragraph = manifestos[party][occurence['paragraph_index']]
    pos = occurence['position']

    stops = paragraph.replace(':!?', '.')
    start = stops.rfind('.', 0, pos + 1)
    end = stops.find('.', pos)
    if end == -1:
        end = None
    sentence = paragraph[start:end]
    send_buttons(sender_id, sentence, buttons=[button_postback('Ob das wohl klappt?', ['no'])])
