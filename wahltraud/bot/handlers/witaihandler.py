
import threading
import json

from .handler import Handler


class WitAiHandler(Handler):
    """
    Handler class to handle wit.ai NLP processed messages.

    Attributes:
        callback (:obj:`callable`): The callback function for this handler.
        entities (:obj:`list[str]`): A list of JSON keys that must be present in the NLP entities

    Args:
        callback (:obj:`callable`): A function that takes ``event, **kwargs`` as arguments.
            It will be called when the :attr:`check_event` has determined that an event should be
            processed by this handler.
        entities (:obj:`list[str]`): A list of JSON keys that must be present in the NLP entities

    """

    def __init__(self, callback, entities=None):
        super().__init__(callback)

        self.entities = entities

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
            entities = json.loads(event['message']['nlp']['entities'])
            self.local.entities = entities

            # Check if the nlp JSON has all the entities we are looking for
            return all(entity in entities for entity in self.entities)

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
