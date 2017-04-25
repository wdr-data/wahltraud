import json
import logging
import os
import csv
from threading import Thread

from flask import Flask, request
import requests
import random
import schedule
import time
from django.utils import timezone

from backend.models import Entry, FacebookUser

# TODO: The idea is simple. When you send "subscribe" to the bot, the bot server would add a record according to the sender_id to their
# database or memory , then the bot server could set a timer to distribute the news messages to those sender_id who have subscribed for the news.

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

        # check if we actually have some input
        if "message" in event and event['message'].get("text", "") != "":
            text = event['message']['text']
            quick_reply = event['message']['quick_reply']['payload']
            if text == '/config':
                reply = "Hier kannst du deine facebook Messenger-ID hinterlegen um automatisch " \
                        "Infos zu den wichtigsten Begriffen rund um die Wahl von uns zu erhalten.\n" \
                        "Wenn du dich registrieren möchtest klicke \"OK\". Du kannst deine Entscheidung jederzet wieder ändern."
                send_text_with_button(sender_id, reply)
            if quick_reply == "subscribe_menue":
                reply = "Hier kannst du deine facebook Messenger-ID hinterlegen um automatisch " \
                        "Infos zu den wichtigsten Begriffen rund um die Wahl von uns zu erhalten.\n" \
                        "Wenn du dich registrieren möchtest klicke \"OK\". Du kannst deine Entscheidung jederzet wieder ändern."
                send_text_with_button(sender_id, reply)
            elif quick_reply == "info":
                random_info = get_data()
                send_text(sender_id, random_info.title)
                if random_info.media != "":
                    image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(random_info.media)
                    send_image(sender_id, image)
                send_text_with_button(sender_id, random_info, 'info')
            else:
                reply = "echo: " + text
                send_text(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "") == "start":
            reply = "Hallo, ich bin Wahltraud! Ich bin dein persönlicher Infobot zur Landtagswahl in NRW 2017!\n" \
                    "Am 14. Mai sind Landtagswahlen! Darum bin ich für die nächsten Tage dein Guide durch den Wahl-Dschungel. " \
                    "Einmal täglich füttere ich dich mit einem wichtigen Begriff zur Landtagswahl in NRW und erkläre, "\
                    "was es damit auf sich hat. \nWenn du genug weißt, kannst du mich auch einfach wieder abbestellen. \n\nBis dann!"
            send_text_and_quickreplies(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "") == "info":
            random_info = get_data()
            send_text(sender_id, random_info.title)
            if random_info.media != "":
                image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(random_info.media)
                send_image(sender_id, image)
            send_text_with_button(sender_id, random_info, 'info')
        elif "postback" in event and event['postback'].get("payload", "").split("#")[0] == "next":
            next_info_title = event['postback'].get("payload", "").split("#")[1]
            next_info = Entry.objects.get(short_title=next_info_title)
            send_text(sender_id, next_info.title)
            send_text_with_button(sender_id, next_info, 'info')
        elif "postback" in event and event['postback'].get("payload", "") == "subscribe_menue" :
            reply = "Hier kannst du deine facebook Messenger-ID hinterlegen um automatisch " \
                    "Infos zu den wichtigsten Begriffen rund um die Wahl von uns zu erhalten.\n" \
                    "Wenn du dich registrieren möchtest klicke \"OK\". Du kannst deine Entscheidung jederzet wieder ändern."
            send_text_with_button(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "") == "subscribe_user":
            subscribe_user(sender_id)
        elif "postback" in event and event['postback'].get("payload", "") == "unsubscribe":
            unsubscribe_user(sender_id)
        elif "postback" in event and event['postback'].get("payload", "") == "impressum":
            reply = "Dies ist ein Produkt des Westdeutschen Rundfunks. Wir befinden uns noch in der Testphase und "\
            "freuen uns über jedes Feedback um uns weiterentwickeln zu können. Danke für Eure Mithilfe! \n"\
            "Redaktion: Miriam Hochhard - Technische Unterstützung: Lisa Achenbach, Patricia Ennenbach, Jannes Hoeke"
            send_text(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "") == "nope":
            reply = "Schade. Vielleicht beim nächsten mal..."
            send_text(sender_id, reply)

def get_data():
    today = timezone.localtime(timezone.now()).date()
    info_list = list(Entry.objects.all())
    random_info = random.choice(info_list)
    logger.debug('Random Info Title: ' + random_info.title)
    return random_info #Info.objects.filter(pub_date__date=today)[:4]

def subscribe_user(user_id):
    if FacebookUser.objects.filter(uid = user_id).exists():
        reply = "Du bist bereits für Push Nachrichten angemeldet."
        send_text(user_id, reply)
    else:
        FacebookUser.objects.create(uid = user_id)
        logger.debug('User with ID ' + str(FacebookUser.objects.latest('add_date')) + ' subscribed.')
        reply = "Danke für deine Anmeldung!\nDu erhältst nun ein tägliches Update jeweils um 8:00 Uhr."
        send_text(user_id, reply)

def unsubscribe_user(user_id):
    if FacebookUser.objects.filter(uid = user_id).exists():
        logger.debug('User with ID ' + str(FacebookUser.objects.get(uid = user_id)) + ' unsubscribed.')
        FacebookUser.objects.get(uid = user_id).delete()
        reply = "Schade, dass du uns verlassen möchtest. Komm gerne wieder, wenn ich dir fehle. \n" \
        "Du wurdest aus der Empfängerliste für Push Benachrichtigungen gestrichen."
        send_text(user_id, reply)
    else:
        reply = "Du bist noch kein Nutzer der Push Nachrichten. Wenn du dich anmelden möchtest wähle \'Anmelden\' im Menü."
        send_text(user_id, reply)

def push_notification():
    data = get_data()
    user_list = FacebookUser.objects.values_list('uid', flat=True)
    for user in user_list:
        logger.debug("Send Push to: " + user)
        reply = "Heute haben wir folgendes Thema für dich:"
        send_text(user, reply)
        send_text(user, data.title)
        if data.media != "":
            image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(data.media)
            send_image(user, image)
        send_text_with_button(user, data, 'info')

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

def send_audio(recipient_id, audio_file):
    """send an audio to a recipient"""
    audio_file = "https://mediandr-a.akamaihd.net/progressive/2017/0302/AU-20170302-0656-0300.mp3"

    recipient = {"id": recipient_id}
    audio = {'url': audio_file}
    filedata = '@' + audio_file + ';type=audio/mp3'

    attachment = {
        'type': 'audio',
        'payload': audio
    }

    message = {'attachment': attachment}

    payload = {
        'recipient': recipient,
        'message': message,
        'filedata': filedata
    }
    send(payload)

def send_generic_template(recipient_id, gifts):
    """send a generic message with title, text, image and buttons"""
    selection = []

    for key in gifts:
        logger.debug(key)
        gift = key

        title = gifts[gift]['title']
        logger.debug(title)
        item_url = gifts[gift]['link']
        image_url = 'http://www1.wdr.de/mediathek/audio/sendereihen-bilder/wdr_sendereihenbild100~_v-Podcast.jpg'
        subtitle = gifts[gift]['teaser']

        listen_Button = {
            'type': 'postback',
            'title': 'ZeitZeichen anhören',
            'payload': 'listen_audio#' + item_url
        }
        download_Button = {
            'type': 'web_url',
            'title': 'ZeitZeichen herunterladen',
            'url': item_url
        }
        visit_Button = {
            'type': 'web_url',
            'url': 'http://www1.wdr.de/radio/wdr5/sendungen/zeitzeichen/index.html',
            'title': 'Zum WDR ZeitZeichen'
        }
        share_Button = {
            'type': 'element_share'
        }
        ### Buttons sind auf max 3 begrenzt! ###
        buttons = []
        buttons.append(listen_Button)
        buttons.append(download_Button)
        buttons.append(share_Button)

        elements = {
            'title': title,
            'item_url': item_url,
            'image_url': image_url,
            'subtitle': subtitle,
            'buttons': buttons
        }

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

def send_text_and_quickreplies(recipient_id, reply):
    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Anmelden',
        'payload' : 'subscribe_menue'
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Info anzeigen',
        'payload' : 'info'
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)

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

def send_text_with_button(recipient_id, info, status="other"):
    """send a message with a button (1-3 buttons possible)"""
    buttons = []
    if status == "info":
        text = info.text
        first_button = {
            'type': 'postback',
            'title': info.link_one.short_title,
            'payload': 'next#' + str(info.link_one.short_title)
        }
        buttons.append(first_button)
        if info.link_three == None and info.link_two != None:
            second_button = {
                'type': 'postback',
                'title': info.link_two.short_title,
                'payload': 'next#' + str(info.link_two.short_title)
            }
            buttons.append(second_button)
        elif info.link_three != None and info.link_two != None:
            second_button = {
                'type': 'postback',
                'title': info.link_two.short_title,
                'payload': 'next#' + str(info.link_two.short_title)
            }
            third_button = {
                'type': 'postback',
                'title': info.link_three.short_title,
                'payload': 'next#' + str(info.link_three.short_title)
            }
            buttons.append(second_button)
            buttons.append(third_button)

    elif status == "other":
        text = info
        ok_button = {
            'type': 'postback',
            'title': 'OK',
            'payload': 'subscribe_user'
        }
        no_button = {
            'type': 'postback',
            'title': 'Nein, danke.',
            'payload': 'nope'
        }
        buttons.append(ok_button)
        buttons.append(no_button)

    load = {
            'template_type': 'button',
            'text': text,
            'buttons': buttons
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
    logger.debug("Payload from send_text_with_button: " + str(payload))
    send(payload)

def send_list_template(infos, recipient_id):
    """send a generic message with a list of choosable informations"""
    selection = []
    count = 0

    for info in infos:
        count += 1
        title = info.headline
        logger.debug(title)

        button = {
            'type': 'postback',
            'title': 'Mehr dazu',
            'payload': 'info#' + str(info.id) + '#' + str(count)
        }
        buttons = []
        buttons.append(button)

        if info.media != "":
            image = "https://infos.data.wdr.de/backend/static/media/" + str(info.media)
            elements = {
                'title': title,
                'image_url': image,
                'buttons': buttons
            }
        else:
            elements = {
                'title': title,
                'buttons': buttons
            }

        selection.append(elements)

    load = {
            'template_type': 'list',
            'top_element_style': 'compact',
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
    logger.debug("JSON Payload: " + json.dumps(payload))
    headers = {'Content-Type': 'application/json'}
    requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_TOKEN,
                  data=json.dumps(payload),
                  headers=headers)


schedule.every().day.at("12:30").do(push_notification)


def schedule_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
schedule_loop_thread.start()

if __name__ == '__main__':
    app.debug = False
    app.run(port=4444)
