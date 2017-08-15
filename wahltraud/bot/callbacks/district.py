import locale

from ..fb import send_buttons, button_postback, send_text
from ..data import by_uuid, by_plz

locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')


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


def send_district(sender_id, district_uuid):
    send_buttons(sender_id,
                 'Ok. Der Wahlkreis deiner Wahl ist {district}'.format(
                     district=by_uuid[district_uuid]['district']),
                 [button_postback("Zeige Wahlkreis-Info",
                                  {'show_district': district_uuid})])


def show_district(event, payload, **kwargs):
    sender_id = event['sender']['id']
    district_uuid = payload['show_district']
    district = by_uuid[district_uuid]

    send_buttons(sender_id, """
Der Wahlkreis "{name}" hat die Nummer {number} und liegt in {state}. Es treten {nr_of_candidates} Kandidaten an, deren Durchschnittsalter {avg_age} Jahre beträgt. 
""".format(
        number=district['district_id'],
        name=district['district'],
        state=district['state'],
        nr_of_candidates=len(district['candidates']),
        avg_age=locale.format('%.1f', 2017.7 - district['meta']['avg_age'])
    ),
                 [
                     button_postback("Kandidaten", {'show_candidates': district_uuid}),
                     button_postback("Bundestagswahl 2013", {'show_13': district_uuid}),
                     # button_postback("Anderer Wahlkreis", {'show_13': district_uuid}),
                 ])

