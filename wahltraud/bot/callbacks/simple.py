
import logging

from fuzzywuzzy import fuzz, process

from pathlib import Path
from backend.models import FacebookUser, Wiki, Push
from ..fb import send_buttons, button_postback, send_text, quick_reply, send_generic, generic_element, button_web_url, button_share, send_attachment
from .shared import get_pushes, schema, send_push

logger = logging.getLogger(__name__)


def get_started(event, **kwargs):
    referral = event.get('postback').get('referral')

    if referral:
        ref = referral.get('ref')
        logging.info('Bot wurde mit neuem User geteilt: ' + ref)

    sender_id = event['sender']['id']
    reply = """
Hallo, ich bin Wahltraud 🐳
Ich informiere dich für die anstehende Bundestagswahl über Kandidaten, Parteien und deren Themen.
Ich erkläre dir gerne, was du mit mir tun kannst. Aber wenn du magst, kannst ud auch einfach drauf los fragen.
Über Push Nachrichten halte ich dich auf dem Laufenden. Um dich für dein automatisches Update zu registrieren, klicke auf \"Anmelden\"."""
    send_buttons(sender_id, reply,
                 buttons=[
                    button_postback('Anmelden', ['subscribe']),
                    button_postback('Erklär mal...', ['about'])
                ])

def about(event, **kwargs):
    sender_id = event['sender']['id']
    reply = "Erfahre alles über Wahltrauds Funktionen. Wähle ein Thema über das du mehr erfahren möchtest."
    send_buttons(sender_id, reply,
                buttons = [
                    button_postback("Kandidatencheck", ['menue_candidates']),
                    button_postback("Wahlprogramme", ['menue_manifesto']),
                    button_postback("Daten", ['menue_data'])
                ])

def push(event, **kwargs):
    sender_id = event['sender']['id']
    data = get_pushes()
    if len(data) == 0:
        reply = 'Dein News Update ist noch in Arbeit. Komme später wieder...'
        send_text(sender_id, reply)
    else:
        schema(data, sender_id)

def share_bot(event, **kwargs):
    sender_id = event['sender']['id']
    reply = "Teile Wahltraud mit deinen Freunden!"

    title = "Wahltraud informiert die über alle Themen rund um die Bundestagswahl 2017."
    subtitle = "Befrage den Messenger Bot zu Kandidaten, Parteien oder Themen rund um die Wahl."
    image_url = "https://scontent-frt3-1.xx.fbcdn.net/v/t1.0-9/17990695_1413687971987169_7350711930902341159_n.jpg?oh=f23c5b76702f9b0819c5d589dcba7e4e&oe=5A300416"
    shared_content = [generic_element(title, subtitle, image_url, buttons = [button_web_url("Schreibe Wahltraud", "https://www.m.me/wahltraud?ref=shared")])]
    message = generic_element("Teile Wahltraud mit deinen Freunden!", buttons = [button_share(shared_content)])

    send_generic(sender_id,
                elements = [message])

def subscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        reply = "Du bist bereits für Push-Nachrichten angemeldet."
        send_text(user_id, reply)

    else:
        FacebookUser.objects.create(uid=user_id)
        logger.debug('subscribed user with ID ' + str(FacebookUser.objects.latest('add_date')))
        reply = """
Danke für deine Anmeldung! Du erhältst nun täglich um 18 Uhr dein Update.\n
Wenn du irgendwann genug Informationen hast, kannst du dich über das Menü natürlich jederzeit wieder abmeden."""
        send_text(user_id, reply)


def unsubscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        logger.debug('deleted user with ID: ' + str(FacebookUser.objects.get(uid=user_id)))
        FacebookUser.objects.get(uid=user_id).delete()
        reply = "Schade, dass du uns verlassen möchtest. Du wurdest aus der Empfängerliste für Push Benachrichtigungen gestrichen."
        send_text(user_id, reply)
    else:
        reply = "Du bist noch kein Nutzer der Push-Nachrichten. Wenn du dich anmelden möchtest wähle \"Anmelden\" über das Menü."
        send_text(user_id, reply)

def menue_candidates(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,
            "Mit dem WDR-Kandidatencheck möchten wir möglichst alle Kandidatinnen und Kandidaten in NRW in einem kurzen Video vorstellen."
            " Es wurden alle Parteien angefragt, aber es haben nicht alle mitgemacht."
            " Damit die Aussagen vergleichbar sind, haben wir allen Teilnehmer dieselben Fragen gestellt. "
            "Hier gibt’s Informationen zum kompletten Projekt:\n"
            "https://blog.wdr.de/ihrewahl/faq-wdr-kandidatencheck-bundestagswahl-2017\n"
"           Wenn du mir eine Postleitzahl aus NRW schreibst, kann ich dir alle verfügbaren Kandidatenchecks aus dem dazugehörigen Wahlkreis zeigen.",
              [quick_reply('Zeige Kandidaten', ['candidate_check_start']),
               quick_reply('Fragen', ['questions'])]
              )

def questions(event,**kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              "Die Interviews stoppen nach exakt vier Minuten. Theoretisch hätten diese 22+6 Fragen beantwortet werden können:\n"
              "https://blog.wdr.de/ihrewahl/die-fragen-stehen-fest/",
              [quick_reply('Zeige Kandidaten', ['candidate_check_start'])]
              )



def menue_manifesto(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              'Was steht eigentlich in so einem Wahlprogramm? '
              'Kaum ein Wähler liest sich ein Wahlprogramm durch. Ich biete Dir einen Einblick '
              'in die einzelnen Programme und zwar zu dem Thema, welches dich interessiert.\n'
              'Du kannst jederzeit ein Schlagwort eintippen und ich schaue nach in welchen Programmen es vorkommt, z.B. Steuern.',
              [quick_reply('Ich habs verstanden', ['manifesto_start']), quick_reply('weiter', {'about_manifesto': 'one'})])

def about_manifesto(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['about_manifesto']

    if state == 'one':
        send_text(sender_id,
                  'Nenne mir ein Schlagwort und eine Partei und ich zeige dir sofort einen Satz aus dem Programm, z.B. Steuern + SPD.',
                  [quick_reply('Ich habs verstanden', ['manifesto_start']), quick_reply('weiter', {'about_manifesto': 'two'})])
    elif state == 'two':
        send_text(sender_id,
                  'Ein einzelner Satz ist oft nicht hilfreich, darum kannst du dir den Kontext anzeigen lassen. '
                  'Falls du richtig neugierig geworden bist, bekommst du auch den Link zum Wahlprogramm.',
                  [quick_reply('Los geht`s', ['manifesto_start'])])

def menue_data(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, """
Um dich mit so vielen Informationen beliefern zu können, musste ich mich natürlich selbst erstmal schlau machen.
Folgende Quellen habe ich dazu verwendet:
- WDR-Kandidatencheck http://kandidatencheck.wdr.de/kandidatencheck/
- abgeordnetenwatch.de https://www.abgeordnetenwatch.de/
- Wahlkompass Digitales http://wahlkompass-digitales.de/
- Bundeswahlleiter https://www.bundeswahlleiter.de/
- infratest dimap https://www.infratest-dimap.de/
- Homepages der Parteien""",
    [quick_reply('Noch was?', ['more_data'])])

def more_data(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, """
Ich arbeite in Kooperation mit Novi, dem Nachrichten-Bot von Funk \nhttps://www.funk.net/
Zudem habe ich mich der Technologie vom WDR Projekt \"Wörter der Wahl\" bedient\nhttps://github.com/wdr-data/woerter-der-wahl
Die Daten auf die ich zurückgreife kannst du dir auch im GitHub Account \"wdr-data\" anschauen\nhttps://github.com/wdr-data
Ich halte mich an die Datenschutzbestimmungen des \"Westdeutschen Rundfunks\"\nhttp://www1.wdr.de/hilfe/datenschutz102.html"""
    )

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

    reply = best_match[0].output
    if not reply:
        if best_match:
            if reply == 'empty':
                reply = "Moment...Ich schaue kurz im Brockhaus nach was {word} bedeutet. Antwort kommt bald.".format(word = text)
    else:
        reply = "Tut mir Leid, darauf habe noch ich keine Antwort. Frag mich die Tage nochmal."

    send_text(user_id, reply)


def apiai_fulfillment(event, **kwargs):
    sender_id = event['sender']['id']

    fulfillment = event['message']['nlp']['result']['fulfillment']
    if fulfillment['speech']:
        send_text(sender_id, fulfillment['speech'])

def push_step(event, payload, **kwargs):
    sender_id = event['sender']['id']
    push_id = payload['push']
    next_state = payload['next_state']

    push_ = Push.objects.get(id=push_id)
    send_push(sender_id, push_, state=next_state)


def sunday_poll(event, **kwargs):
    sender_id = event['sender']['id']

    quick_replies = [
        quick_reply(
            'infratest dimap',
            ['menue_data']
        ),
        quick_reply(
            'Info Parteien',
            {'show_parties': 'etabliert'}
        )
    ]

    send_text(sender_id,
              'Hier das Ergebnis der aktuellen Sonntagsfrage von infratest dimap vom 31. August.'
              )

    send_attachment(
        sender_id,
        'https://infos.data.wdr.de:8080/static/bot/Sonntagsfrage_aktuell.jpg'
    )

    send_text(sender_id,
              'Wenn du etwas zu einer bestimmten Partei wissen möchtest, gib einfach ihren Namen ein.',
              quick_replies
              )


