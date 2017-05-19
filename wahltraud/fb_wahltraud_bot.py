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
import xml.etree.ElementTree as ET

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
            elif quick_reply.split("#")[0] == "kandidaten":
                plz = quick_reply.split("#")[1]
                wahlkreis = get_wahlkreis(plz)
                send_kandidatencheck(sender_id, wahlkreis)
            elif quick_reply.split("#")[0] == "winner":
                winner = quick_reply.split("#")[1]
                kreis = quick_reply.split("#")[2]
                send_winner(sender_id, winner, kreis)
            elif quick_reply.split("#")[0] == 'whywinner':
                kreis = quick_reply.split("#")[1]
                voting, winner, candidate_voting = get_vote(kreis)
                send_candidate_voting(sender_id, candidate_voting, winner, kreis)
            elif quick_reply.split("#")[0] == "more_voting":
                kreis = quick_reply.split("#")[1]
                kreis = str(kreis).zfill(3)
                voting, winner, candidate_voting = get_vote(kreis)
                send_complete_voting(sender_id, voting, winner, kreis)
            elif quick_reply.split("#")[0] == 'send_voting':
                plz = quick_reply.split("#")[1]
                kreis = quick_reply.split('#')[2]
                logger.debug("wahlkreis: " + kreis)
                wahlkreis = get_wahlkreis(plz)
                for wk, gebiet in wahlkreis.items():
                    logger.debug("wahlkreis auswahl:" + str(wk))
                    if wk == int(kreis):
                        voting, winner, candidate_voting = get_vote(kreis)
                        if not voting:
                            text = "Leider habe ich für deinen Wahlkreis noch kein Ergebnis. Versuche es später erneut."
                            send_text(sender_id, text)
                        else:
                            send_voting(sender_id, wk, voting, winner, gebiet)
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
            if Entry.objects.filter(short_title__iexact=text).exists():
                info = Entry.objects.get(short_title__iexact=text)
                if info.web_link:
                    send_generic_template(sender_id, info)
                else:
                    send_text(sender_id, info.title)
                    if info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, info)
            elif len(text) == 5 and text.isdigit():
            #     logger.info("plz eingabe: " + str(text))
            #     wahlkreis = get_wahlkreis(text)
            #     kreis = set()
            #     titel = set()
            #     for wk, gebiet in wahlkreis.items():
            #         kreis.add(wk)
            #         titel.add(gebiet)
            #     logger.info("kreis: " + str(kreis) + " titel: " + str(titel))
            #     if len(kreis) == 1:
            #         send_kandidatencheck(sender_id, wahlkreis)
            #     elif len(kreis) > 1:
            #         send_wahlkreis(sender_id, text)
            #     else:
            #         text = "Falls das deine Postleitzahl ist, kenne ich sie nicht.\nBitte überprüfe deine Eingabe. "\
            #                 "Ich kann nur Postleitzahlen aus NRW verarbeiten und den entsprechenden Wahlkreis suchen."
            #         send_text(sender_id, text)
            # elif text.startswith('#'):       #len(text) == 5 and text.isdigit():
                plz = text
                logger.info("plz eingabe: " + str(plz))
                wahlkreis = get_wahlkreis(plz)
                kreis = list()
                titel = list()
                for wk, gebiet in wahlkreis.items():
                    wk = str(wk).zfill(3)
                    kreis.append(wk)
                    titel.append(gebiet)
                logger.info("kreis: " + str(kreis) + " titel: " + str(titel))
                if len(kreis) == 1:
                    for element in kreis:
                        for t in titel:
                            titel = t
                        voting, winner, candidate_voting = get_vote(element)
                        if not voting:
                            text = "Leider habe ich für deinen Wahlkreis noch kein Ergebnis. Versuche es später erneut."
                            send_text(sender_id, text)
                        else:
                            send_voting(sender_id, kreis, voting, winner, titel)
                elif len(kreis) > 1:
                    send_wahlkreis(sender_id, plz, kreis, titel)
                else:
                    text = "Falls das deine Postleitzahl ist, kenne ich sie nicht.\nBitte überprüfe deine Eingabe. "\
                            "Ich kann nur Postleitzahlen aus NRW verarbeiten und den entsprechenden Wahlkreis suchen."
                    send_text(sender_id, text)
            elif text == "Schick mir eine Info zur Wahl!".lower() or text == "Info".lower():
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
            elif text == "Danke".lower() or text == "Danke schön".lower():
                reply = "Gern geschehen. 😊 "
                send_text(sender_id, reply)
            else:
                logger.info('Feedback: ' + text)
                if datetime.now() > datetime(2017, 5, 16, 19, 59):
                    text = "Danke für dein Feedback 🙂 Das habe ich mir notiert 📝"
                    send_text(sender_id, text)
                else:
                    text_reply(sender_id)
        elif "postback" in event and event['postback'].get("payload", "") != "":
            payload = event['postback']['payload']
            if payload == "start":
                send_greeting(sender_id)
            elif payload == "info":
                info = get_data()
                if info.web_link:
                    send_generic_template(sender_id, info)
                else:
                    send_text(sender_id, info.title)
                    if info.media != "":
                        image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)
                        send_image(sender_id, image)
                    send_info(sender_id, info)
            elif payload == "wahlkreis":
                info = Entry.objects.get(short_title="Wahl-Ergebnisse")
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
        info = Entry.objects.get(short_title="Danke")
    elif info.count() >= 1:
        info = random.choice(info)
    return info

def get_wahlkreis(plz):
    with open('plz_wk_unique.json') as data_file:
        data = json.load(data_file)

    result = dict()
    for element in data:
        if any(plz in s for s in element["plzGebiete"]):
            result[element["wk"]] = element["gebiet"]
    return result

def send_wahlkreis(recipient_id, plz, kreis, titel):
    text = "Ich habe zu deiner Postleitzahl mehrere Wahlkreise gefunden: \n"
    for t in titel:
        text += str(t) + '\n'
    text += "Bitte prüfe selbst, welchem Wahlkreis du zugeordnet bist."
    quickreplies = []
    i = 1
    for k in kreis:
        reply_one = {
            'content_type' : 'text',
            'title' : 'Zeige ' + str(i) + '. Wahlkreis',
            'payload' : 'send_voting#' + str(plz) + '#' + str(k)
        }
        i+= 1
        quickreplies.append(reply_one)
    send_text_and_quickreplies(text, quickreplies, recipient_id)

def get_vote(kreis):
    result_candidate = {}
    result_party = {}
    sieger = []
    #for key in kreis:
    xml_data = "xml/erg_05" + str(kreis).zfill(3) + ".xml"
    logger.info(xml_data)
    if os.path.isfile(xml_data):
        tree = ET.parse(xml_data)
        root = tree.getroot()
        logger.info(root.tag)
        for gebiet in root.findall('Gebietsergebnis'):
            for direkt in gebiet.findall('Direktergebnis'):
                for gewinner in direkt.findall('Gewinner'):
                    sieger = [gewinner.get('Name'), gewinner.get('Gruppe'), gewinner.get('Prozent')]
            for gruppe in gebiet.findall('Gruppenergebnis'):
                if gruppe.get('Gruppenart') == 'PARTEI':
                    party = gruppe.get('Name')
                    candidate = gruppe.get('Direktkandidat')
                    for ergebnis in gruppe.findall('Stimmergebnis'):
                        if ergebnis.get('Stimmart') == 'ERST':
                            first_vote = ergebnis.get('Prozent')
                            if first_vote == 'n/a':
                                pass
                            else:
                                result_candidate[candidate] = float(first_vote)
                        elif ergebnis.get('Stimmart') == 'ZWEIT':
                            second_vote = ergebnis.get('Prozent')
                            if second_vote == 'n/a':
                                pass
                            else:
                                result_party[party] = float(second_vote)

    return result_party, sieger, result_candidate

def send_voting(recipient_id, kreis, voting, winner, wahlkreis):
    if type(kreis) is not int:
        for k in kreis:
            kreis = k
    image_title = "erg_05"+str(kreis).zfill(3)+".jpg"
    image = "https://infos.data.wdr.de:8080/backend/static/jpg/" + image_title
    response = requests.head(image)
    if response.status_code != 404:
        logger.debug("send image: " + image_title)
        send_image(recipient_id, image)
    text = "Für deinen Wahlkreis " + str(wahlkreis) + " haben diese Parteien mehr als 5 % der Zweitstimmen bekommen:\n"

    for k,v in reversed(sorted(voting.items(), key=lambda x: (x[1],x[0]))):
        if v == 'n/a':
            pass
        elif float(v) < 5:
            pass
        else:
            text += k + ": " + str(v) + "%\n"

    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Weitere Parteien',
        'payload' : 'more_voting#' + str(kreis)
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Direktkandidat',
        'payload' : 'winner#' + str(winner) + '#' + str(kreis)
    }
    reply_three = {
        'content_type' : 'text',
        'title' : 'Und die Erststimme?',
        'payload' : 'whywinner#' + str(kreis)
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)
    quickreplies.append(reply_three)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

def send_complete_voting(recipient_id, voting, winner, kreis):
    text = "Alle Parteien im Überblick:\n"
    for k,v in reversed(sorted(voting.items(), key=lambda x: (x[1],x[0]))):
        if v == 'n/a':
            pass
        else:
            text += k + ": " + str(v) + "%\n"

    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Direktkandidat',
        'payload' : 'winner#' + str(winner) + '#' + str(kreis)
    }
    quickreplies.append(reply_one)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

def send_candidate_voting(recipient_id, candidate_voting, winner, kreis):
    text = "Mit der Erststimme haben die Wähler eine Kandidat/In direkt gewählt. Der Politiker "\
        "oder die Politikerin mit den meisten Erststimmen zieht direkt in den Landtag ein. "\
        "Das ist doch ein Grund zum Strahlen ?!  ☀ \n\nSo haben die Kandidaten in deinem Wahlkreis abgeschnitten: \n"
    for k,v in reversed(sorted(candidate_voting.items(), key=lambda x: (x[1],x[0]))):
        if v == 'n/a':
            pass
        else:
            text += k + ": " + str(v) + "%\n"

    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Alle Parteien',
        'payload' : 'more_voting#' + str(kreis)
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Sieger anzeigen',
        'payload' : 'winner#' + str(winner) + '#' + str(kreis)
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

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
    if data.short_title == 'Danke':
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)
    for user in user_list:
        reply = "Heute haben wir folgendes Thema für dich:"
        send_text(user, reply)
        if data.web_link:
            send_generic_template(user, data)
            sleep(1)
        else:
            send_text(user, data.title)
            if data.media != "":
                image = "https://infos.data.wdr.de:8080/backend/static/media/" + str(data.media)
                send_image(user, image)
            send_info(user, data)
            sleep(1)
    logger.info("pushed messages to " + str(len(user_list)) + " users")

def send_greeting(recipient_id):
    text = "Hallo, ich bin Wahltraud! 🤖 Ich bin dein persönlicher Infobot zur Landtagswahl in NRW 2017!\n" \
            "Am 14. Mai waren die Landtagswahlen! Darum bin ich dein Guide durch den Wahl-Dschungel. " \
            "Einmal täglich füttere ich dich mit einem wichtigen Begriff zur Landtagswahl in NRW und erkläre, was es damit auf sich hat."

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

# def really_request(recipient_id):
#     text = "Es gibt täglich nur einen neuen Satz an Informationen. Möchtest du trotzdem jetzt schon deine Info haben?"
#     quickreplies = []
#     reply_one = {
#         'content_type' : 'text',
#         'title' : 'Ja',
#         'payload' : 'info_now'
#     }
#     reply_two = {
#         'content_type' : 'text',
#         'title' : 'Nein, später bitte',
#         'payload' : 'info_later'
#     }
#     quickreplies.append(reply_one)
#     quickreplies.append(reply_two)
#
#     send_text_and_quickreplies(text, quickreplies, recipient_id)

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

    default_action = {
        'type': 'web_url',
        'url': info.web_link
    }
    if info.media != "":
        image_url = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)

        elements = {
            'title': title,
            'image_url': image_url,
            'subtitle': subtitle,
            'default_action': default_action
        }
    else:
        elements = {
            'title': title,
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

def send_kandidatencheck(recipient_id, result):
    """send a link with title, text, image and link-url"""
    """title and subtitle are limited to 80 characters"""
    info = Entry.objects.get(short_title="Dein Wahlkreis")

    for key, value in result.items():
        title = info.title + " " + value
        subtitle = info.text
        link = info.web_link + str(key)

        default_action = {
            'type': 'web_url',
            'url': link
        }
        if info.media != "":
            image_url = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)

            elements = {
                'title': title,
                'image_url': image_url,
                'subtitle': subtitle,
                'default_action': default_action
            }
        else:
            elements = {
                'title': title,
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

def send_winner(recipient_id, winner, kreis):
    """send a link with title, text, image and link-url"""
    """title and subtitle are limited to 80 characters"""
    info = Entry.objects.get(short_title="Sieger im Wahlkreis")

    subtitle = info.text
    winner = eval(winner)
    if winner:
        title = info.title + " " + winner[0]
        winner_short = winner[0].split(' ')[1]
        link = info.web_link + str(winner_short)
    else:
        title = info.title
        link = "http://kandidatencheck.wdr.de/kandidatencheck/"

    default_action = {
        'type': 'web_url',
        'url': link
    }
    if info.media != "":
        image_url = "https://infos.data.wdr.de:8080/backend/static/media/" + str(info.media)

        elements = {
            'title': title,
            'image_url': image_url,
            'subtitle': subtitle,
            'default_action': default_action
        }
    else:
        elements = {
            'title': title,
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

    text = "Was nun?"
    quickreplies = []
    reply_one = {
        'content_type' : 'text',
        'title' : 'Zeige alle Parteien',
        'payload' : 'more_voting#' + str(kreis)
    }
    reply_two = {
        'content_type' : 'text',
        'title' : 'Zeige alle Kandidaten',
        'payload' : 'whywinner#' + str(kreis)
    }
    quickreplies.append(reply_one)
    quickreplies.append(reply_two)

    send_text_and_quickreplies(text, quickreplies, recipient_id)

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
