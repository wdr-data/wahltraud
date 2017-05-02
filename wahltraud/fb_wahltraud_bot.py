import json
import logging
import os
import csv
from threading import Thread

from flask import Flask, request
import requests
import random
import schedule
from time import sleep
from datetime import datetime, time, date

from backend.models import Entry, FacebookUser

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger.info('FB Wahltraud Bot Logging')

PAGE_TOKEN = os.environ.get('WAHLTRAUD_PAGE_TOKEN', 'not set')
HUB_VERIFY_TOKEN = os.environ.get('WAHLTRAUD_HUB_VERIFY_TOKEN', 'not set')

app = Flask(__name__)


@app.route('/testbot', methods=["GET"])
def confirm():
    if request.args['hub.verify_token'] == HUB_VERIFY_TOKEN:
        return request.args['hub.challenge']
    return 'Hello World!'


@app.route('/testbot', methods=["POST"])
def receive_message():
    data = request.json
    handle_messages(data)
    return "ok"


def handle_messages(data):
    """handle all incoming messages"""
    messaging_events = data['entry'][0]['messaging']
    logger.debug(messaging_events)
    for event in messaging_events:
        sender_id = event['sender']['id']
        info_list = list(Entry.objects.all())
        # check if we actually have some input
        if "message" in event and event['message'].get("quick_reply", "") != "":
            quick_reply = event['message']['quick_reply']['payload']
            if Entry.objects.filter(short_title=quick_reply).exists():
                next_info = Entry.objects.get(short_title=quick_reply)
                logger.info('weitere Info angefragt: ' + next_info.title)
                if next_info.web_link:
                    send_generic_template(sender_id, next_info)
                else:
                    send_text(sender_id, next_info.title)
                    if next_info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(next_info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, next_info)
            elif quick_reply == "info":
                info = get_data()
                if info.web_link:
                    send_generic_template(sender_id, info)
                else:
                    send_text(sender_id, info.title)
                    if info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, info)
            elif quick_reply == "subscribe_menue":
                subscribe_process(sender_id)
            elif quick_reply == "subscribe":
                subscribe_user(sender_id)
            elif quick_reply == "unsubscribe":
                unsubscribe_user(sender_id)
            elif quick_reply == "nope":
                reply = "Schade. Vielleicht beim nächsten Mal..."
                send_text(sender_id, reply)
            elif quick_reply == "info_now":
                info = get_data()
                if info.web_link:
                    send_generic_template(sender_id, info)
                else:
                    send_text(sender_id, info.title)
                    if info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, info)
            elif quick_reply == "info_later":
                reply = "Okay, ich melde mich später mit deinem Update."
                send_text(sender_id, reply)
        elif "message" in event and event['message'].get("text", "") != "" and event['message'].get('quick_reply') == None:
            text = event['message']['text'].lower()
            if text == "Schick mir eine Info zur Wahl!".lower() or text == "Info".lower():
                info = get_data()
                if info.web_link:
                    send_generic_template(sender_id, info)
                else:
                    send_text(sender_id, info.title)
                    if info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, info)
            elif text == "Anmelden".lower() or text == "Abmelden".lower():
                subscribe_process(sender_id)
            elif text == "Teilen".lower():
                share(sender_id)
            elif text == "Impressum".lower():
                reply = "Dies ist ein Produkt des Westdeutschen Rundfunks. Wir befinden uns noch in der Testphase und "\
                "freuen uns über jedes Feedback um uns weiterentwickeln zu können. \n"\
                "Sende uns Feedback über die Messener Option \"Feedback senden\". Danke für Deine Mithilfe! \n"\
                "Redaktion: Miriam Hochhard - Technische Umsetzung: Lisa Achenbach, Patricia Ennenbach, Jannes Hoeke"
                send_text(sender_id, reply)
            elif text == "Hallo".lower() or text == "Hey".lower() or text == "Hi".lower() or text == "Moin".lower():
                reply = "Hallo! Einen schönen Tag wünsche ich dir."
                send_text(sender_id, reply)
            elif text == "Tschüss".lower() or text == "Tschö".lower() or text == "Ciao".lower() or text == "Auf Wiedersehen".lower():
                reply = "Tschüss, mach es gut."
                send_text(sender_id, reply)
            elif text == "/link":
                today = date(2017,5,3)
                info = Entry.objects.get(pub_date__date=today)
                if info.web_link:
                    send_generic_template(sender_id, info)
                else:
                    send_text(sender_id, info.title)
                    if info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, info)
            else:
                text_reply(sender_id)
        elif "postback" in event and event['postback'].get("payload", "") != "":
            payload = event['postback']['payload']
            if payload == "start":
                send_greeting(sender_id)
            elif payload == "info":
                if datetime.now().time() < time(20,00):
                    really_request(sender_id)
                else:
                    info = get_data()
                    if info.web_link:
                        send_generic_template(sender_id, info)
                    else:
                        send_text(sender_id, info.title)
                        if info.media != "":
                            image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                            send_image(sender_id, image)
                        send_info(sender_id, info)
            elif payload == "subscribe_menue" :
                subscribe_process(sender_id)
            elif payload == "share_bot":
                share(sender_id)
            elif payload == "impressum":
                reply = "Dies ist ein Produkt des Westdeutschen Rundfunks. http://www1.wdr.de/impressum/index.html \n\n" \
                "Wir befinden uns noch in der Testphase und freuen uns über jedes Feedback, um uns weiterentwickeln zu können. \n"\
                "Sende uns Feedback über die Messener Option \"Feedback senden\". Danke für Deine Mithilfe! \n\n"\
                "Redaktion: Miriam Hochhard \nTechnische Umsetzung: Lisa Achenbach, Patricia Ennenbach, Jannes Höke"
                send_text(sender_id, reply)
        else:
            text_reply(sender_id)

def get_data():
    today = datetime.now().date()
    info = Entry.objects.filter(pub_date__date=today)
    if info.count() == 0:
        info = Entry.objects.get(short_title="Zeitplan")
    elif info.count() >= 1:
        info = random.choice(info)
    return info

def subscribe_process(recipient_id):
    text = "Melde dich an, um automatisch Infos zu den wichtigsten Begriffen rund um die Wahl von mir zu erhalten. " \
            "Wenn du dich registrieren möchtest klicke \"Anmelden\". \n\n" \
            "Du kannst diese Entscheidung jederzet wieder ändern oder jetzt erstmal auf später verschieben. " \
            "Wenn du keine automatischen Nachrichten mehr von uns erhalten möchtest klicke \"Abmelden\". \n\n" \
            "Du findest diese Optionen im Menü unter \"An-/Abmelden\""
    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Anmelden',
        'payload' : 'subscribe'
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Abmelden',
        'payload' : 'unsubscribe'
    }
    reply_three = {
        'content_type' : 'text',
        'title' : 'Jetzt nicht',
        'payload' : 'nope'
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)
    quickreplies.append(reply_three)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

def subscribe_user(user_id):
    if FacebookUser.objects.filter(uid = user_id).exists():
        reply = "Du bist bereits für die automatischen Nachrichten angemeldet."
        send_text(user_id, reply)
    else:
        FacebookUser.objects.create(uid = user_id)
        logger.info('added user with ID: ' + str(FacebookUser.objects.latest('add_date')))
        now_time = datetime.now().time()
        if now_time >= time(20,00):
            reply = "Danke für deine Anmeldung! 😃 Du erhältst nun ein tägliches Update jeweils um 20:00 Uhr. \n"\
                    "Hier ist die heutige Info..."
            send_text(user_id, reply)
            info = get_data()
            send_text(user_id, info.title)
            send_info(user_id, info)
        else:
            reply = "Danke für deine Anmeldung! 😃 Du erhältst nun ein tägliches Update jeweils um 20:00 Uhr.\nBis später"
            send_text(user_id, reply)

def unsubscribe_user(user_id):
    if FacebookUser.objects.filter(uid = user_id).exists():
        logger.info('deleted user with ID: ' + str(FacebookUser.objects.get(uid = user_id)))
        FacebookUser.objects.get(uid = user_id).delete()
        reply = "Schade, dass du uns verlassen möchtest. Komm gerne wieder, wenn ich dir fehle. 👋\n" \
                "Du wurdest aus der Empfängerliste für automatische Nachrichten gestrichen."
        send_text(user_id, reply)
    else:
        reply = "Du bist noch kein Nutzer der Push-Nachrichten. Wenn du dich anmelden möchtest wähle \"Anmelden\" im Menü " \
                "oder klicke jetzt auf \"Anmelden\"."
        quickreplies = []
        reply_one = {
            'content_type' : 'text',
            'title' : 'Anmelden',
            'payload' : 'subscribe'
        }
        quickreplies.append(reply_one)
        send_text_and_quickreplies(reply, quickreplies, user_id)

def push_notification():
    data = get_data()
    user_list = FacebookUser.objects.values_list('uid', flat=True)
    for user in user_list:
        reply = "Heute haben wir folgendes Thema für dich:"
        send_text(user, reply)
        if data.web_link:
            send_generic_template(user, data)
        else:
            send_text(user, data.title)
            if data.media != "":
                image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(data.media)
                send_image(user, image)
            send_info(user, data)
    logger.info("pushed messages to " + str(len(user_list)) + " users")

def send_greeting(recipient_id):
    text = "Hallo, ich bin Wahltraud! 🤖 Ich bin dein persönlicher Infobot zur Landtagswahl in NRW 2017!\n" \
            "Am 14. Mai sind Landtagswahlen! Darum bin ich für die nächsten Tage dein Guide durch den Wahl-Dschungel. " \
            "Einmal täglich füttere ich dich mit einem wichtigen Begriff zur Landtagswahl in NRW und erkläre, "\
            "was es damit auf sich hat. \nWenn du genug weißt, kannst du mich auch einfach wieder abbestellen."

    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Anmelden',
        'payload' : 'subscribe_menue'
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Begriff anzeigen',
        'payload' : 'info'
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

def text_reply(recipient_id):
    text = "Ich bin nur ein einfaches Geschöpf und ich habe deine Nachricht nicht verstanden. " \
            "Nutze bitte die Buttons bzw. das Menü um mit mir zu kommunizieren.\n\n" \
            "Möchtest du eine Begriffserklärung zur Wahl von mir bekommen?"

    quickreplies = []
    reply = {
        'content_type' : 'text',
        'title' : 'Begriff anzeigen',
        'payload' : 'info'
    }
    quickreplies.append(reply)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

def really_request(recipient_id):
    text = "Es gibt täglich nur einen neuen Satz an Informationen. Möchtest du trotzdem jetzt schon deine Info haben?"
    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Ja',
        'payload' : 'info_now'
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Nein, später bitte',
        'payload' : 'info_later'
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

def send_info(recipient_id, info):
    text = info.text

    quickreplies = []
    if info.link_one != None:
        first = {
            'content_type' : 'text',
            'title': info.link_one.short_title,
            'payload': str(info.link_one.short_title)
        }
        quickreplies.append(first)
        if info.link_three == None and info.link_two != None:
            second = {
                'content_type' : 'text',
                'title': info.link_two.short_title,
                'payload': str(info.link_two.short_title)
            }
            quickreplies.append(second)
        elif info.link_three != None and info.link_two != None:
            second = {
                'content_type' : 'text',
                'title': info.link_two.short_title,
                'payload': str(info.link_two.short_title)
            }
            third = {
                'content_type' : 'text',
                'title': info.link_three.short_title,
                'payload': str(info.link_three.short_title)
            }
            quickreplies.append(second)
            quickreplies.append(third)

    if quickreplies:
        send_text_and_quickreplies(text, quickreplies, recipient_id)
    else:
        send_text(recipient_id, text)

def send_text(recipient_id, text):
    """send a text message to a recipient"""
    recipient = {'id': recipient_id}
    message = {'text': text}
    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)

def send_image(recipient_id, image_url):
    """send an image to a recipient"""

    recipient = {'id': recipient_id}

    # create an image object
    image = {'url': image_url}

    # add the image object to an attachment of type "image"
    attachment = {
        'type': 'image',
        'payload': image
    }

    # add the attachment to a message instead of "text"
    message = {'attachment': attachment}

    # now create the final payload with the recipient
    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)

def share(recipient_id):
    logger.info("shared button requeted")
    """send a generic message with title, text, image and buttons"""
    shared_title = 'Hallo, ich bin Wahltraud! 🤖 Ich bin dein Infobot zur Landtagswahl in NRW 2017!'
    shared_subtitle = 'Am 14. Mai sind Landtagswahlen und ich bin dein Guide durch den Wahl-Dschungel.'
    shared_button = {
        'type': 'web_url',
        'url': 'https://m.me/wahltraud',
        'title': 'Try Wahltraud'
    }
    shared_buttons = []
    shared_buttons.append(shared_button)

    shared_elements = {
        'title': shared_title,
        'subtitle': shared_subtitle,
        'buttons': shared_buttons
    }
    shared_selection = []
    shared_selection.append(shared_elements)

    shared_load = {
        'template_type': 'generic',
        'elements': shared_selection
    }
    shared_attachment = {
        'type': 'template',
        'payload': shared_load
    }
    shared_message = {'attachment': shared_attachment}

    title = 'Teile mich mit deinen Freunden!'
    subtitle = 'Wahltraud freut sich über jeden neuen User... Klicke auf \"Teilen\".'

    share_Button = {
        'type': 'element_share',
        'share_contents': shared_message
    }
    ### Buttons sind auf max 3 begrenzt! ###
    buttons = []
    buttons.append(share_Button)

    elements = {
        'title': title,
        'subtitle': subtitle,
        'buttons': buttons
    }
    selection = []
    selection.append(elements)

    load = {
        'template_type': 'generic',
        'elements': selection
    }
    attachment = {
        'type': 'template',
        'payload': load
    }

    message = {'attachment': attachment}

    recipient = {'id': recipient_id}

    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)

def send_text_and_quickreplies(reply, quickreplies, recipient_id):
    message = {
        'text' : reply,
        'quick_replies' : quickreplies
    }

    recipient = {'id': recipient_id}

    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)

def send_generic_template(recipient_id, info):
    """send a link with title, text, image and link-url"""
    """title and subtitle are limited to 80 characters"""

    title = info.title
    subtitle = info.text
    if info.media != "":
        image_url = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)

    default_action = {
        'type': 'web_url',
        'url': info.web_link
    }

    elements = {
        'title': title,
        'image_url': image_url,
        'subtitle': subtitle,
        'default_action': default_action
    }
    selection = []
    selection.append(elements)

    load = {
            'template_type': 'generic',
            'elements': selection
        }

    attachment = {
        'type': 'template',
        'payload': load
    }

    message = {'attachment': attachment}

    recipient = {'id': recipient_id}

    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)

def send(payload):
    """send a payload via the graph API"""
    #logger.debug("JSON Payload: " + json.dumps(payload))
    headers = {'Content-Type': 'application/json'}
    requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_TOKEN,
                  data=json.dumps(payload),
                  headers=headers)


schedule.every().day.at("20:00").do(push_notification)

def schedule_loop():
    while True:
        schedule.run_pending()
        sleep(1)

schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
schedule_loop_thread.start()

if __name__ == '__main__':
    app.debug = False
    app.run(port=4444)
