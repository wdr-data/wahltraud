import json
import logging
import os
import csv

from flask import Flask, request
import requests
#from django.utils.timezone import localtime, now
from django.utils import timezone

from backend.models import Entry

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
            logger.debug('received message')
            text = event['message']['text']
            if text == '/info':
                reply = "Heute haben wir folgende Themen für dich:"
                send_text(sender_id, reply)
                data = get_data()
                send_list_template(data, sender_id)
            elif text == '/config':
                reply = "Hier kannst du deine facebook Messenger-ID hinterlegen um automatisch ein tägliches Update von uns zu erhalten.\n" \
                        "Wenn du dich registiren möchtest klicke \"OK\". Du kannst deine Entscheidung jederzet wieder ändern."
                send_text_with_button(sender_id, reply)
            else:
                reply = "echo: " + text
                send_text(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "") == "start":
            reply = "Herzlich willkommen zum 1LIVE InfoMessenger. \n\n" \
                    "Hier bekommst Du alle Infos geliefert, die Du wissen musst, um mitreden zu " \
                    "können, selbst die, von denen Du nicht weißt, dass Du sie wissen wolltest" \
                    " :) \n\nWas Du dafür tun musst: Fast nichts. Tippe \"/info\" um dein " \
                    "Update zu bekommen."
            send_text(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "").split("#")[0] == "info":
            requested_info_id = event['postback'].get("payload", "").split("#")[1]
            info = Info.objects.get(id=int(requested_info_id))
            status = "intro"
            send_text(sender_id, info.headline)
            if info.media != "":
                image = "https://infos.data.wdr.de/backend/static/media/" + str(info.media)
                send_image(sender_id, image)
            logger.debug("status in postback: " + status)
            send_text_with_button(sender_id, info, status)
        elif "postback" in event and event['postback'].get("payload", "").split("#")[0] == "more":
            requested_info_id = event['postback'].get("payload", "").split("#")[2]
            info = Info.objects.get(id=int(requested_info_id))
            logger.debug(event['postback'].get("payload", "").split("#")[1])
            if event['postback'].get("payload", "").split("#")[1] == "0":
                status = "one"
            elif event['postback'].get("payload", "").split("#")[1] == "1":
                status = "two"
            send_text_with_button(sender_id, info, status)
            # reply = "Hier folgen weitere Infos zum Thema."
            # send_text(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "").split("#")[0] == "subscribe":
            subscribe_user(sender_id)
            reply = "Danke für deine Anmeldung!\nDu erhältst nun ein tägliches Update jeweils um 8:00 Uhr wochentags."
            send_text(sender_id, reply)
        elif "postback" in event and event['postback'].get("payload", "") == "back":
            data = get_data()
            send_list_template(data, sender_id)

def get_data():
    today = timezone.localtime(timezone.now()).date()
    return Info.objects.filter(pub_date__date=today)[:4]

def subscribe_user(user_id):
    FacebookUser.objects.create(uid = user_id)
    logger.debug('User with ID ' + FacebookUser.objects.latest('add_date') + ' subscribed.')

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

def send_text_with_button(recipient_id, info, status="other"):
    """send a message with a button (1-3 buttons possible)"""
    if status == "intro":
        status_id = 0
        text = info.intro_text
        button_title = info.first_question
    elif status == "one":
        status_id = 1
        text = info.first_text
        button_title = info.second_question
    elif status == "two":
        status_id = 2
        text = info.second_text
        button_title = "None"
    elif status == "other":
        status_id = 3
        text = info
        button_title = "OK"

    logger.debug("Text: " + str(text) + ", info.introtext: " + str(info.intro_text))
    logger.debug("Status at send_text_with_button: " + str(status) + " " + str(status_id))

    if status_id == 3:
        task = 'subscribe#' + recipient_id
    else:
        task = 'more#' + str(status_id) + '#' + str(info.id)

    more_button = {
        'type': 'postback',
        'title': button_title,
        'payload': task
    }

    back_button = {
        'type': 'postback',
        'title': 'Zurück',
        'payload': 'back'
    }
    buttons = []
    if status_id == 2:
        buttons.append(back_button)
    else:
        buttons.append(more_button)
        buttons.append(back_button)

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


if __name__ == '__main__':
    app.debug = False
    app.run(port=4444)
