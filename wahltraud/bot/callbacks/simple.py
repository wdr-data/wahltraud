
import logging

from fuzzywuzzy import fuzz, process

from backend.models import FacebookUser, Wiki, Push
from ..fb import send_buttons, button_postback, send_text, quick_reply
from .shared import get_pushes, schema, send_push

logger = logging.getLogger(__name__)


def get_started(event, **kwargs):
    reply = """
    Hallo, ich bin Wahltraud.
    Um dich für dein automatisches Update zu registrieren, klicke auf \"OK\"."""
    sender_id = event['sender']['id']
    send_buttons(sender_id, reply,
                 buttons=[button_postback('OK', ['subscribe'])])


def push(event, **kwargs):
    sender_id = event['sender']['id']
    data = get_pushes()
    if len(data) == 0:
        reply = 'Dein News Update ist noch in Arbeit. Komme später wieder...'
        send_text(sender_id, reply)
    else:
        schema(data, sender_id)


def subscribe_user(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        reply = "Du bist bereits für Push-Nachrichten angemeldet."
        send_text(user_id, reply)

    else:
        FacebookUser.objects.create(uid=user_id)
        logger.debug('User with ID ' + str(FacebookUser.objects.latest('add_date')) + ' subscribed.')
        reply = "Danke für deine Anmeldung!\nDu erhältst nun ein tägliches Update."
        send_text(user_id, reply)


def unsubscribe_user(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        logger.debug('deleted user with ID: ' + str(FacebookUser.objects.get(uid=user_id)))
        FacebookUser.objects.get(uid=user_id).delete()
        reply = "Schade, dass du uns verlassen möchtest. Du wurdest aus der Empfängerliste für Push Benachrichtigungen gestrichen."
        send_text(user_id, reply)
    else:
        reply = "Du bist noch kein Nutzer der Push-Nachrichten. Wenn du dich anmelden möchtest wähle \"Anmelden\" im Menü."
        send_text(user_id, reply)

def menue_manifesto(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              'Was steht eigentlich in so einem Wahlprogramm? '
              'Kaum ein Wähler liest sich ein Wahlprogramm durch. Ich biete Dir an dieser Stelle einen Einblick '
              'in die einzelnen Programme und zwar zu dem Thema, welches dich interessiert.',
              [quick_reply('weiter', {'about_manifesto': 'one'})])

def about_manifesto(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['about_manifesto']

    replies = list
    replies.append([quick_reply('Ich habs verstanden', 'end')])

    if state == 'one':
        replies.append([quick_reply('weiter', {'about_manifesto': 'two'}]))
        send_text(sender_id,
                  'Du kannst jederzeit ein Wahlthema eintippen und ich schaue nach in welchen Programmen es vorkommt. \nz.B. Steuern',
                  replies)
    elif state == 'two':
        replies.append([quick_reply('weiter', {'about_manifesto': 'three'}]))
        send_text(sender_id,
                  'Nenne mir ein Wort und eine Partei und ich zeige dir sofort einen Satz aus dem Programm. \nz.B. Steuern + SPD',
                  replies)

def story(event, payload, **kwargs):
    sender_id = event['sender']['id']
    push_id = payload['push_id']
    next_state = payload['next_state']
    data = Push.objects.get(id=push_id)
    send_push(sender_id, data, next_state)


def wiki(event, parameters, **kwargs):
    user_id = event['sender']['id']
    text = parameters.get('wiki')

    wikis = Wiki.objects.all()

    best_match = process.extractOne(
        text,
        wikis,
        scorer=fuzz.token_set_ratio,
        score_cutoff=50)

    if best_match:
        reply = best_match[0].output

    else:
        reply = "Tut mir Leid, darauf habe noch ich keine Antwort. Frag mich die Tage nochmal " + text + "."

    send_text(user_id, reply)


def apiai_fulfillment(event, **kwargs):
    sender_id = event['sender']['id']

    fulfillment = event['message']['nlp']['result']['fulfillment']
    if fulfillment['speech']:
        send_text(sender_id, fulfillment['speech'])
