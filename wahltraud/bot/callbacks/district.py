
from ..fb import send_buttons, button_postback, send_text
from ..data import by_uuid, by_plz


def find_district(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    plz = parameters['plz']

    if not plz:
        reply = """
Viele Wege führen zum Wahlkreis deiner Wahl. Am schnellsten geht es, indem du mir 
deine Postleitzahl schreibst."""

        send_text(sender_id, reply)

    else:
        district_uuids = by_plz.get(plz)

        if not district_uuids:
            send_text(sender_id, "Diese PLZ sagt mir nichts...")

        elif len(district_uuids) == 1:
            send_district(sender_id, district_uuids.pop())

        else:
            send_buttons(sender_id,
                         'Welchen Wahlkreis meinst du?',
                         [button_postback(district['district'],
                                          {'show_district': district['district_uuid']})
                          for district in
                          [by_uuid[uuid] for uuid in district_uuids]]
                         )


def show_district(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_district']
    send_text(sender_id, "Zeige Wahlkreis %s" % district_uuid)


def send_district(sender_id, district_uuid):
    send_buttons(sender_id,
                 'Ok. Der Wahlkreis deiner Wahl ist {district}'.format(
                     district=by_uuid[district_uuid]['name']),
                 [button_postback("Zeige Wahlkreis-Info",
                                  {'show_district': district_uuid})])
