import logging
from threading import Thread
from time import sleep
import os
import json

import schedule
#from django.utils.timezone import localtime, now
from apiai import ApiAI

from backend.models import Push, FacebookUser, Wiki
from .fb import send_text, send_buttons, button_postback, PAGE_TOKEN
from .handlers.payloadhandler import PayloadHandler
from .handlers.texthandler import TextHandler
from .handlers.apiaihandler import ApiAiHandler
from .callbacks.simple import (get_started, push, subscribe_user, unsubscribe_user, wiki, story,
                               apiai_fulfillment, about_manifesto, menue_manifesto, subscribe_menue, share_bot, about)
from .callbacks.shared import (get_pushes, get_breaking, send_push, schema)
from .callbacks import candidate, district, browse_lists, manifesto, party

# TODO: The idea is simple. When you send "subscribe" to the bot, the bot server would add a record according to the sender_id to their
# database or memory , then the bot server could set a timer to distribute the news messages to those sender_id who have subscribed for the news.

# Enable logging
logger = logging.getLogger(__name__)

logger.info('FB Wahltraud Logging')

API_AI_TOKEN = os.environ.get('WAHLTRAUD_API_AI_TOKEN', 'na')

ADMINS = [
    1781215881903416,  # Christian
    1450422691688898,  # Jannes
]


def make_event_handler():
    ai = ApiAI(API_AI_TOKEN)

    handlers = [
        PayloadHandler(story, ['push_id', 'next_state']),
        PayloadHandler(get_started, ['wahltraud_start_payload']),
        PayloadHandler(about, ['about']),
        PayloadHandler(subscribe_menue, ['subscribe_menue']),
        PayloadHandler(share_bot, ['share_bot']),
        PayloadHandler(subscribe_user, ['subscribe']),
        PayloadHandler(unsubscribe_user, ['unsubscribe']),
        PayloadHandler(push, ['push']),
        ApiAiHandler(wiki, 'wiki'),
        PayloadHandler(menue_manifesto, ['menue_manifesto']),
        PayloadHandler(about_manifesto, ['about_manifesto']),
        ApiAiHandler(candidate.basics, 'kandidat'),
        ApiAiHandler(party.basics, 'parteien'),
        PayloadHandler(party.show_parties, ['show_parties']),
        ApiAiHandler(candidate.candidate_check, 'kandidatencheck'),
        PayloadHandler(district.intro_district, ['intro_district']),
        PayloadHandler(candidate.intro_candidate, ['intro_candidate']),
        PayloadHandler(district.show_13, ['show_13']),
        PayloadHandler(candidate.search_candidate_list, ['search_candidate_list']),
        PayloadHandler(candidate.payload_basics, ['payload_basics']),
        PayloadHandler(candidate.more_infos_nrw, ['more_infos_nrw']),
        PayloadHandler(candidate.no_video_to_show, ['no_video_to_show']),
        PayloadHandler(candidate.show_video, ['show_video']),
        PayloadHandler(district.show_candidates, ['show_candidates']),
        ApiAiHandler(district.find_district, 'wahlkreis_finder'),
        PayloadHandler(district.show_district, ['show_district']),
        ApiAiHandler(browse_lists.apiai, 'liste'),
        PayloadHandler(browse_lists.intro_lists, ['intro_lists']),
        PayloadHandler(browse_lists.select_state, ['select_state']),
        PayloadHandler(browse_lists.select_party, ['select_party']),
        PayloadHandler(browse_lists.show_list, ['show_list', 'state', 'party']),
        PayloadHandler(manifesto.manifesto_start, ['manifesto_start']),
        PayloadHandler(manifesto.show_word_payload, ['show_word']),
        PayloadHandler(manifesto.show_sentence_payload, ['show_sentence']),
        PayloadHandler(manifesto.show_paragraph, ['show_paragraph']),
        PayloadHandler(manifesto.show_manifesto, ['show_manifesto']),
        ApiAiHandler(manifesto.show_word_apiai, 'wahlprogramm'),
        TextHandler(apiai_fulfillment, '.*'),
    ]

    def event_handler(data):
        """handle all incoming messages"""
        messaging_events = data['entry'][0]['messaging']
        logger.debug(messaging_events)

        for event in messaging_events:
            message = event.get('message')

            if message:
                text = message.get('text')

                if (text is not None
                    and event.get('postback') is None
                    and message.get('quick_reply') is None):

                    request = ai.text_request()
                    request.lang = 'de'
                    request.query = text
                    request.session_id = event['sender']['id']
                    response = request.getresponse()
                    nlp = json.loads(response.read().decode())
                    logging.info(nlp)
                    message['nlp'] = nlp

            for handler in handlers:
                try:
                    if handler.check_event(event):
                        try:
                            handler.handle_event(event)

                        except Exception as e:
                            logging.exception("Handling event failed")

                            try:
                                sender_id = event['sender']['id']
                                send_text(
                                    sender_id,
                                    'Huppsala, das hat nicht funktioniert :('
                                )

                                if int(sender_id) in ADMINS:
                                    txt = str(e)
                                    txt = txt.replace(PAGE_TOKEN, '[redacted]')
                                    txt = txt.replace(API_AI_TOKEN, '[redacted]')
                                    send_text(sender_id, txt)
                            except:
                                pass

                        finally:
                            break

                except:
                    logging.exception("Testing handler failed")

    return event_handler

handle_events = make_event_handler()


def push_notification():
    data = get_pushes()

    if not data:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    for user in user_list:
        logger.debug("Send Push to: " + user)
        schema(data, user)
        sleep(1)


def push_breaking():
    data = get_breaking()

    if data is None or data.delivered:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    for user in user_list:
        logger.debug("Send Push to: " + user)
        # media = '327430241009143'
        # send_attachment(user, media, 'image')
        send_push(user, data)
        sleep(1)

    data.delivered = True
    data.save(update_fields=['delivered'])


schedule.every(30).seconds.do(push_breaking)
schedule.every().day.at("20:00").do(push_notification)
schedule.every().day.at("08:00").do(push_notification)


def schedule_loop():
    while True:
        schedule.run_pending()
        sleep(1)

schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
schedule_loop_thread.start()
