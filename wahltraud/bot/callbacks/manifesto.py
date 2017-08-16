import locale

from ..fb import send_buttons, button_postback, send_text, send_list, list_element, quick_reply
from ..data import words

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


def search_word_apiai(event, parameters, **kwargs):
    word = parameters.get('thema')
    party = parameters.get('partei')

    if not party:
        search_word(event, word)


def search_word_payload(event, payload, **kwargs):
    word = payload.get('search_word')
    search_word(event, word)


def search_word(event, word):
    sender_id = event['sender']['id']
    stat = words.get(word)

    if not stat:
        send_text(sender_id, 'Hmmm... dieses Wort erkenne ich nicht.')
        return

    send_text(
        sender_id,
        'Wusstest Du, dass das Wort "{word}" insgesamt {n} mal in den Wahlprogrammen aller '
        'Parteien vorkommt?'.format(
            word=word,
            n=stat['count']
        ))