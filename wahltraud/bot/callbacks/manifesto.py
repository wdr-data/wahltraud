import locale
import random
import logging
from re import findall

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import all_words, random_words_list, party_abbr, party_rev, manifestos, by_party

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def manifesto_start(event, **kwargs):
    sender_id = event['sender']['id']

    random_words = list()
    for i in range(10):
        word = random.choice(random_words_list)
        random_words.append(quick_reply(word, {'show_word': word}))

    send_text(
        sender_id,
        "Lass mich für dich die Programme nach einem Wort durchsuchen. "
        "Schreib mir einfach ein Wort, welches dich interessiert.",
        random_words
    )


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
        for party, seg in sorted(segs.items(), key=lambda kv: kv[1]['share'], reverse=True)
    ][offset:offset + num_words]

    if len(segs) - offset > num_words:
        button = button_postback("Mehr anzeigen",
                                 {'show_word': word,
                                  'offset': offset + num_words})
    else:
        button = button_postback("Neues Wort", ['manifesto_start'])

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

    if party not in party_abbr:
        party = party_rev[party]

    occurences = all_words[word]['segments'][party]['occurence']
    occurence = random.choice(occurences)
    paragraph = manifestos[party][occurence['paragraph_index']]
    pos = occurence['position']

    stops = paragraph.replace(':!?', '.')
    start = stops.rfind('.', 0, pos + 1) + 1
    end = stops.find('.', pos) + 1
    if not end:
        end = None
    sentence = paragraph[start:end].strip()
    send_text(sender_id, "Hier ein zufällig gewählter Satz aus dem Wahlprogramm der "
                         "Partei \"%s\"" % party_abbr[party])
    send_text(
        sender_id,
        '"%s"' % sentence,
        quick_replies=[
            quick_reply(
                'Satz im Kontext',
                {'show_paragraph': occurence['paragraph_index'], 'party': party, 'word': word}
            ),
            quick_reply(
                'Noch ein Satz',
                {'show_sentence': word, 'party': party}
            ),
            quick_reply(
                'Neues Wort',
                ['manifesto_start']
            ),
        ])


def show_paragraph(event, payload, **kwargs):
    sender_id = event['sender']['id']
    paragraph = payload['show_paragraph']
    party = payload['party']
    word = payload['word']
    paragraph = manifestos[party][paragraph]

    if party in by_party[party]:
        party_link = quick_reply(
            'Parteiprgramm zeigen',
            {'show_link': party}
        )
    logger.debug('Link Parteiprogramm: ' + str(party_link))

    send_text(
        sender_id,
        '"%s"' % paragraph,
        quick_replies=[
            quick_reply(
                'Noch ein Satz',
                {'show_sentence': word, 'party': party}
            ),
            quick_reply(
                'Neues Wort',
                ['manifesto_start']
            ),

        ])
