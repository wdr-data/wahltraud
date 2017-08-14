
import threading
import json

from .handler import Handler


class ApiAiHandler(Handler):
    """
    Handler class to handle api.ai NLP processed messages.

    Attributes:
        callback (:obj:`callable`): The callback function for this handler.
        entities (:obj:`list[str]`): A list of JSON keys that must be present in the NLP entities

    Args:
        callback (:obj:`callable`): A function that takes ``event, **kwargs`` as arguments.
            It will be called when the :attr:`check_event` has determined that an event should be
            processed by this handler.
        intent (:obj:`str`): Intent name to handle

    """

    def __init__(self, callback, intent=None):
        super().__init__(callback)

        self.intent = intent

        # We use this to carry data from check_event to handle_event in multi-threaded environments
        self.local = threading.local()

    def check_event(self, event):
        """
        Determines whether an event should be passed to this handlers :attr:`callback`.

        Args:
            event (:obj:`dict`): Incoming Messenger JSON dict.

        Returns:
            :obj:`bool`
        """
        message = event.get('message')

        if not message:
            return False

        nlp = message.get('nlp')

        if nlp is not None:
            intent = json.loads(event['message']['nlp']['metadata']['intentName'])
            self.local.intent = intent

            return intent == self.intent

        else:
            return False

    def handle_event(self, event):
        """
        Send the event to the :attr:`callback`.

        Args:
            event (:obj:`dict`): Incoming Facebook event.
        """

        kwargs = dict()
        kwargs['entities'] = self.local.entities

        return self.callback(event, **kwargs)
