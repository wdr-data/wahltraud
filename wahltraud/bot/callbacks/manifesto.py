import locale
import random
import logging
from re import findall

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import all_words, random_words_list, party_abbr, party_rev, manifestos, find_party, get_digital_words
from .party import show_electorial

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def manifesto_start(event, **kwargs):
    sender_id = event['sender']['id']

    random_words = list()
    for i in range(10):
        word = random.choice(random_words_list)
        random_words.append(quick_reply(word, {'show_word': word}))

    send_text(
        sender_id,'''
        Wähle eines der folgenden Wörter aus oder schreib mir direkt ein Wort, welches dich interessiert.
        Tipp: Suche immer auch nach ähnlichen Schlagwörtern zu einem Thema. Wenn ein Wort in einem Programm nicht vorkommt, so ist dies nicht gleichbedeutend damit, dass die Partei ein Thema nicht behandelt!
         ''',
        random_words
    )


def show_word_apiai(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    word = parameters.get('thema')
    party = parameters.get('partei')


    if not word and not party:
        manifesto_start(event, **kwargs)
    elif not word:
         show_electorial(event, {'show_electorial': party})
    elif not party:
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
        send_text(sender_id, 'Hmmm... dieses Wort finde ich in keinem Programm.')
        return

    logger.info('Wahlprogramm - Wort: {word}'.format(word=word))
    segs = stat['segments']

    if len(segs) == 1:
        party, seg = next(iter(segs.items()))
        send_buttons(
            sender_id,
            'Das Wort "{word}" kommt nur im Wahlprogramm der Partei "{party}" vor.'.format(
                word=word,
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
            'Das Wort "{word}" kommt insgesamt {n} mal in allen Wahlprogrammen vor. '
            'Hier eine Auflistung nach relativer Häufigkeit.'.format(
                word=word,
                n=stat['count']
            ))

    send_list(sender_id, elements, button=button)


def show_sentence(event, word, party, **kwargs):
    sender_id = event['sender']['id']
    stat = all_words.get(word)

    if not stat:
        send_text(sender_id, 'Hmmm... dieses Wort finde ich in dem gewünschten Programm nicht.')
        return

    if party not in party_abbr:
        if party not in party_rev:
            send_text(
                sender_id,
                'Zu dieser Partei liegt mir leider kein Wahlprogramm vor. '
                'Versuche es doch mit einer anderen Partei.',
            )
            return
        else:
            party = party_rev[party]

    logger.debug('Wahlprogramm - Wort: {word} Partei: {party}'.format(word=word, party=party))
    try:
        occurences = all_words[word]['segments'][party]['occurence']
    except:
        quick_replies = [
            quick_reply(
                "Andere Parteien?",
                {'show_word': word,
                 'offset': 0}
            ),
            quick_reply(
                'Neues Wort',
                ['manifesto_start']
            )
        ]

        party_manifesto = find_party(party_abbr[party])
        if party_manifesto['skript'] is not None:
            quick_replies.insert(
                2,
                quick_reply(
                    'Wahlprogramm lesen',
                    {'show_manifesto': party_manifesto['skript'], 'party': party}
                )
            )

        send_text(
            sender_id,
            "Das Wort \"{word}\" kommt nicht im Programm der {party} vor. "
            "Versuche es nochmal mit einem ähnlichem Schlagwort.".format(
                word=word, party=party_abbr[party]),
            quick_replies
        )
        return

    occurence = random.choice(occurences)
    paragraph = manifestos[party][occurence['paragraph_index']]
    pos = occurence['position']

    stops = paragraph.replace(':!?', '.')
    start = stops.rfind('.', 0, pos + 1) + 1
    end = stops.find('.', pos) + 1
    if not end:
        end = None
    sentence = paragraph[start:end].strip()
    send_text(sender_id, "Hier ein Satz mit dem Wort \"{word}\" aus dem Wahlprogramm der "
                         "Partei \"{party}\"".format(
            party=party_abbr[party],
            word = word)
              )
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

    quick_replies = [
        quick_reply(
            'Noch ein Satz',
            {'show_sentence': word, 'party': party}
        ),
        quick_reply(
            'Neues Wort',
            ['manifesto_start']
        ),
        quick_reply(
            'Info ' + party_abbr[party],
            {'show_party_options': party_abbr[party]}
        )
    ]

    party_manifesto = find_party(party_abbr[party])

    if party_manifesto['skript'] is not None:
        quick_replies.insert(
            2,
            quick_reply(
                'Wahlprogramm lesen',
                {'show_manifesto': party_manifesto['skript'], 'party': party}
            )
        )

    if word in get_digital_words():
        quick_replies.insert(
            1,
            quick_reply(
                'Wahlkompass-Digitales',
                {'show_manifesto': word, 'party': party}
            )
        )

    send_text(sender_id, '"%s"' % paragraph, quick_replies)


def show_manifesto(event, payload, **kwargs):
    sender_id = event['sender']['id']
    link = payload['show_manifesto']
    party = payload['party']


    logger.info('Wahlprogramm - Link angefordert')

    quick_replies = [
        quick_reply(
            'Neues Wort',
            ['manifesto_start']
        ),
        quick_reply(
            'Info ' + party_abbr[party],
            {'show_party_options': party_abbr[party]}
        )
    ]

    if link in get_digital_words():
        reply = """
            Du hast dich für ein Schlagwort entschieden, welches mit der Digitalisierung in Zusammenhang steht.
            Beim Wahlkompass-Digitales, kannst du alle Wahlprogramme nach digitalen Themen durchsuchen und direkt vergleichen:\n
            {link}
            """.format(
                link="http://wahlkompass-digitales.de/")
    else:
        reply = "Hier findest du das vollständige Wahlprogramm\n\"{party}\": {link}".format(
                party=party_abbr[party],
                link=link)

    send_text(
        sender_id, reply, quick_replies
    )