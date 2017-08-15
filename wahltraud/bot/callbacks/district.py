
from ..fb import send_buttons, button_postback, send_text
from ..data import by_uuid


def find_district(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    plz = parameters['plz']

    if not plz:
        reply = """
Viele Wege führen zum Wahlkreis deiner Wahl. Am schnellsten geht es, indem du mir 
deine Postleitzahl schreibst."""

        send_text(sender_id, reply)

    elif plz:
        send_district(sender_id, plz)  # TODO


def show_district(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_district']
    send_text(sender_id, "Zeige Wahlkreis %s" % district_uuid)


def send_district(sender_id, district_uuid):
    send_buttons(sender_id,
                 'Ok. Der Wahlkreis deiner Wahl ist {district}'.format(
                     district=by_uuid[district_uuid]['name']),
                 button_postback("Zeige Wahlkreis-Info",
                                 {'show_district': district_uuid}))
