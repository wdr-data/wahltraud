import logging
from threading import Thread
from time import sleep

import schedule
#from django.utils.timezone import localtime, now
from fuzzywuzzy import fuzz, process

from backend.models import Push, FacebookUser, Wiki
from .fb import send_text, send_buttons, button_postback
from .handlers.payloadhandler import PayloadHandler
from .handlers.texthandler import TextHandler
from .callbacks.simple import (get_started, push, subscribe_user, unsubscribe_user, wiki, story)
from .callbacks.shared import (get_pushes, get_breaking, send_push, schema)

# TODO: The idea is simple. When you send "subscribe" to the bot, the bot server would add a record according to the sender_id to their
# database or memory , then the bot server could set a timer to distribute the news messages to those sender_id who have subscribed for the news.

# Enable logging
logger = logging.getLogger(__name__)

logger.info('FB Wahltraud Logging')


def make_event_handler():
    handlers = [
        PayloadHandler(story, ['push_id', 'next_state']),
        PayloadHandler(get_started, ['wahltraud_start_payload']),
        PayloadHandler(subscribe_user, ['subscribe']),
        PayloadHandler(unsubscribe_user, ['unsubscribe']),
        PayloadHandler(push, ['push']),
        TextHandler(wiki, '(.*)'),
    ]

    def event_handler(data):
        """handle all incoming messages"""
        messaging_events = data['entry'][0]['messaging']
        logger.debug(messaging_events)

        for event in messaging_events:
            for handler in handlers:
                try:
                    if handler.check_event(event):
                        try:
                            handler.handle_event(event)

                        except:
                            logging.exception("Handling event failed")

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