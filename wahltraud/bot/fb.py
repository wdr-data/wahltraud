import os
import json
import logging

import requests

PAGE_TOKEN = os.environ.get('WAHLTRAUD_PAGE_TOKEN', 'na')
logger = logging.getLogger(__name__)


def send_text(recipient_id, text, quick_replies=None):
    """
    Sends a text message to a recipient, optionally with quick replies
    :param recipient_id: The user ID of the recipient
    :param text: The text to be sent
    :param quick_replies: A list of quick replies (optional)
    """
    message = {'text': text}

    if quick_replies is not None:
        message['quick_replies'] = quick_replies

    payload = {
        'recipient': {
            'id': recipient_id,
        },
        'message': message,
    }

    send(payload)


def send_buttons(recipient_id, text, buttons):
    """
    Sends a text message with up to 3 buttons to a recipient
    :param recipient_id: The user ID of the recipient
    :param text: The text to be sent (max. 640 characters)
    :param buttons: Up to 3 buttons
    """
    payload = {
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': text,
                    'buttons': buttons
                }
            }
        }
    }

    send(payload)


def button_postback(title, payload):
    """
    Creates a dict to use with send_buttons
    :param title: Button title
    :param payload: Button payload
    :return: dict
    """
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload)

    return {
        'type': 'postback',
        'title': title,
        'payload': payload,
    }


def button_url(title, url, webview_height_ratio='full'):
    """
    Creates a dict to use with send_buttons
    :param title: Button title
    :param url: Button URL
    :param webview_height_ratio: Height of the Webview. Valid values: compact, tall, full.
    :return: dict
    """
    return {
        'type': 'web_url',
        'title': title,
        'url': url,
        'webview_height_ratio': webview_height_ratio
    }


def quick_reply(title, payload, image_url=None):
    """
    Creates a dict to use with send_text
    :param title: The title of the quick reply
    :param payload: The payload
    :param image_url: The image url (optional)
    :return: dict
    """
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload)

    payload_ = {
        'content_type': 'text',
        'title': title,
        'payload': payload,
      }
    
    if image_url:
        payload_['image_url'] = image_url
        
    return payload_


def send_attachment(recipient_id, attachment_id, type):
    """
    Sends an attachment via ID
    :param recipient_id: The user ID of the recipient
    :param attachment_id: The attachment ID returned by upload_attachment
    :param type: The attachment type (see guess_attachment_type)
    """

    recipient = {'id': recipient_id}

    # create a media object
    media = {'attachment_id': attachment_id}

    # add the image object to an attachment of type "image"
    attachment = {
        'type': type,
        'payload': media
    }

    # add the attachment to a message instead of "text"
    message = {'attachment': attachment}

    # now create the final payload with the recipient
    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)


def send(payload):
    """Sends a payload via the graph API"""
    logger.debug("JSON Payload: " + json.dumps(payload))
    headers = {'Content-Type': 'application/json'}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_TOKEN,
                      data=json.dumps(payload),
                      headers=headers)
    logger.debug(r.content.decode())


def upload_attachment(url):
    """Uploads an attachment and returns the attachment ID, or None if the upload fails"""
    payload = {
        "message": {
            "attachment": {
                "type": guess_attachment_type(url),
                "payload": {
                    "url": url,
                    "is_reusable": True,
                }
            }
        }
    }
    logger.debug("JSON Payload: " + json.dumps(payload))
    headers = {'Content-Type': 'application/json'}
    r = requests.post(
        "https://graph.facebook.com/v2.6/me/message_attachments?access_token=" + PAGE_TOKEN,
        data=json.dumps(payload),
        headers=headers)

    try:
        return json.loads(r.content.decode())['attachment_id']

    except:
        return None


def guess_attachment_type(filename):
    """Guesses the attachment type from the file extension"""
    ext = os.path.splitext(filename)[1].lower()
    types = {
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.mp4': 'video',
        '.mp3': 'audio',
    }

    return types.get(ext, None)
