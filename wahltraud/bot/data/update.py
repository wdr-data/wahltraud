import json
import requests
from shutil import copyfile
from datetime import datetime
import numpy as np
import pandas as pd
import re
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup


def update():

    update_abgewatch = False
    update_alle = True
    update_wahlkreis = False



    # download data from abgeordnetenwatch

    # option =  (1 == "deputies", 2 == "candidates", 3 = "constituencies

    parliament = "Bundestag"
    kind_of_people  = "candidates"
    output_file_abgeordnetenwatch = "abgeordnetenwatch.json"
    abgewatch_data_file = output_file_abgeordnetenwatch
    alle_kandidaten_json = "alle_kandidaten.json"
    nrw_kandidatencheck_json = "kandidatencheck_erweitert_0109.json"
    wahlkreis_info_json = "wahlkreis_info.json"

    if update_abgewatch:
        # make backup json
        date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        copyfile(output_file_abgeordnetenwatch, "abgeordnetenwatch_backup_"+date+".json")
        print("update ageordnetenwatch")
        abgeordnetenapi(parliament, kind_of_people , output_file_abgeordnetenwatch )
        print("update abgeordnetenwatch done")



    if update_alle:
    # create all_kandidaten


        print("update alle_kandidaten")
        abgewatch_to_alle(abgewatch_data_file, nrw_kandidatencheck_json, alle_kandidaten_json)
        print("update " + alle_kandidaten_json + " done")

    
    if update_wahlkreis:
        # create wahlkreis_info

        # make backup
        date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        #copyfile(wahlkreis_info_json , "wahlkreis_info_backup_"+date+".json")

        # make wahlkreis_info_json
        print("wahlkreis_info")
        wahlkreis_info(alle_kandidaten_json, wahlkreis_info_json)
        print("update " + wahlkreis_info_json + " done")

    return
    


def wahlkreis_info(alle_kandidaten_json, wahlkreis_info_json):
    """
    ARGS:
        alle_kandidaten_json (str):  
        wahlkreis_info_json (str):   file name of the creation of wahlkreis_info

    """  
    
    # set take_city to be true
    take_city = True
    api = 0   #  0: use file ort_plz_wk, 1 use api
    
     
    with open(alle_kandidaten_json) as file:
        alle = json.load(file)
    
    wahlkreis_plz_json = "wahlkreis_plz.json"
    bundesland_wahlkreisId = "bundesland_wahlkreisId.json"
    ort_plz_wk = "ort_plz_wk.json"
    

    

    with open(wahlkreis_plz_json) as file2:
        wk = json.load(file2)

    with open(bundesland_wahlkreisId) as f:
        wk_bundesland = json.load(f)

    with open(ort_plz_wk) as f:
        ort_plz_wk = json.load(f)

    wkinfo = []
    for item in wk["constituencies"]:

        wahlkreisId = item["number"]
        wahlkreis_uuid = item["uuid"]
        # plz, orte
        plz_ort = plz_ort_finder(item,  ort_plz_wk, take_city),
        kandmeta = kandidaten_und_meta(wahlkreis_uuid,alle)

        wkinfo.append({ "district_id": item["number"],
                                "district":  item["name"],
                                "election_13": wahl2013(wahlkreisId),
                                "uuid": item["uuid"],
                                "state": bundesland_finder(wahlkreisId,wk_bundesland),
                                "plz": plz_ort[0][0],
                                "cities": plz_ort[0][1],
                                "candidates":kandmeta[0],
                                "meta": kandmeta[1]
                                 })
    wkinfo2 = {}
    wkinfo2["districts"] = wkinfo

    wkinfo2["election13"] = wahl2013('999') # result deutschland gesamt


    with open(wahlkreis_info_json, "w", encoding="utf8") as outfile:  
        json.dump(wkinfo2, outfile, ensure_ascii=False)
    
    return




def trafo_kandidatencheck(short_json, long_json, output_json, pic_size = "m"):
    """ Adds the picture URL from the long Kandidatencheck_json to the short_candidatencheckjson
    Args:
        short_json (str): the file of the short and nice json
        long_json (str): the file of the long, ugly json
        output_json (str): the name of the new created output file
        pic_size (str):  pic size \in ["l","m","s","xs"] 
        
    Yields:
        creates a file with the new picture
        if there is no picture for the candidate, it writes an empty string "" instead.
        
        Further, we take away the list from the parteien key, resulting in a single string

    """
    with open(short_json) as input_file:
        short = json.load(input_file)

    with open(long_json) as input_file:
        long = json.load(input_file)
    
    for index,item in enumerate(short["list"]):
        # take away the list from parteien
        short["list"][index]["parteien"] = short["list"][index]["parteien"][0]

    # get picture from erweiterte version
        for look in long["k"]:
            if look["id"] == item["id"]:
                try:
                    short["list"][index]["img"] = look["img"][pic_size]
                except:
                    short["list"][index]["img"] = None


    # get videolink


    #


    # write extended short json in output file
    with open(output_json, "w", encoding="utf8") as output_file:
        json.dump(short,output_file,  ensure_ascii=False)
    
    return 



    
    
    
def abgeordnetenapi(parliament, option, file_name):

    # option = value 1-3 or one of the strings
    if option == 1:
        list_kind = "deputies"
    elif option ==2:
        list_kind = "candidates"
    elif option == 3:
        list_kind = "constituencies"
    else:
        list_kind = option

    # get ID for the parliaments of interest
    r = requests.get("https://www.abgeordnetenwatch.de/api/parliaments.json")
    parliaments = r.json()

    for parli in parliaments["parliaments"]:
        if parli["name"] == parliament:
            id_parliament= parli["uuid"]
      
    print("request adress ist\n https://www.abgeordnetenwatch.de/api/parliament/"+id_parliament+"/"+list_kind+".json")

    # get data from current Bundestag
    r = requests.get("https://www.abgeordnetenwatch.de/api/parliament/"+id_parliament+"/"+list_kind+".json").json()
    with open(file_name, "w") as output_file:
        json.dump(r, output_file)
    output_file.close()

    print("Daten wurden erfolgreich von der abgeordnetenwatch API geladen und in den entsprechenden Dateien gespeichert.")

    return


def give_nrw_info(last_name,first_name,row):
    """
    Args 
        last_name (str): last_name from abgeordnetenwatch
        first_name (str): first_name from abgeordnetenwatch
        wk_id (str): wahlkreis ID from agbeordnetenwatch
    Yields
        corresponding Id (str) from nrw kandidaten_check
    """

    pic_size = "m"

    nrw_info = {}
    #nrw_info["id"] = row["id"]
    try:
        nrw_info["pledges"] = row["wv"]
    except:
        nrw_info["pledges"]  = None
    try:
        nrw_info["profession"] = row["b"]
    except:
        nrw_info["profession"] = None

    try:
        nrw_info["img"] = "http:"+ row["img"][pic_size]
    except:
        nrw_info["img"] = None

    try:
        string = requests.get(row["v"]["adp"]).text
        m = re.search("14\d/(.+?),(.+?).mp4", string)
        split = m.group(0).split(",")
        file_id = split[0] + split[4]
        nrw_info["video"] = "http://ondemand-ww.wdr.de/medp/fsk0/" + file_id + ".mp4"
    except:
        nrw_info["video"] = None

    try:
        nrw_info["interests"] = row["i"]
    except:
        nrw_info["interests"] = None
    try:
        nrw_info["zusatz"] =  row["zt"] + " " + row["z"]
    except:
        nrw_info["zusatz"] = None



    return nrw_info




def abgewatch_to_alle(kandidaten_alle, nrw_kandidaten, output_file):
    """
    Args:
        kandidaten_alle (str): 
        nrw_kandidaten (str):
        output_file (str)
        
    Yields
        stores a json in output_file with the same keys as nrw_kandidaten. 
        E.g.:   {"alter": "1997",
                 "beruf": "Angestellte",
                 "degree": None,
                 "education": None,
                 "id": "",
                 "listenplatz": "13",
                 "nachname": "Hügelschäfer",
                 "parteien": "DIE LINKE",
                 "uuid": "1c2427a9-7561-45a1-8d9a-0f147429849c",
                 "vorname": "Kristin",
                 "wahkreis_uuid": "57ca45cc-2b61-4010-a8aa-4a87e83119dc",
                 "wahlkreis": "Odenwald",
                 "wahlkreisId": "187"}

    Note. No PLZ, since this can be related by wahlkreisId
    """
    data = pd.read_csv('btw17_all_candidates_buwale.csv', delimiter = ';')
    data = data.where((pd.notnull(data)), None)
    data.replace('-', 'AD', inplace=True)

    # for district uuid in nrw candidates
    with open("wahlkreis_info.json") as data_file:
        district = json.load(data_file)

    # List of candidates in parliament
    with open('./results/gewaehlte.xml') as f:
        ywinner = BeautifulSoup(f, "lxml-xml")


    # laden des abgeordnetenwatch kandidaten files
    with open(kandidaten_alle) as data_file:
        data_abewatch = json.load(data_file)
    with open(nrw_kandidaten) as file:
        nrw = json.load(file)
    # erstelle liste
    data_list = []
    vornamen = []
    nachnamen = []
    all_party = []
    all_party_control = []

    party_map = {"gesundheitsf": "Gesundheitsforschung",
                 "fdp": "FDP",
                 "piraten": "PIRATEN",
                 "partei": "Die PARTEI",
                 "spd": "SPD",
                 "linke": "DIE LINKE",
                 "gruene": "GRÜNE",
                 "cdu": "CDU",
                 "oedp": "ÖDP",
                 "dib": "DiB",
                 "dkp": "DKP",
                 "bge": "BGE",
                 "afd": "AfD",
                 "add": "AD",
                 "mlpd": "MLPD",
                 "fw": "FREIE WÄHLER",
                 "v_partei": "V-Partei³",
                 "none": "Parteilos",
                 "tierschutz": "Tierschutzpartei",
                 "npd": "NPD",
                 "humanisten": "Die Humanisten",
                 "sgp": "SGP",
                 "dm": "DM",
                 "va": "Volksabstimmung",
                 "violette": "DIE VIOLETTEN"
                 }

    # how to erstelle kandidaten_file
    countwin = 0
    for index, item in data.iterrows():


        temp = {
                #personal
                "profession":  item['Beruf'],
                #"education": item["personal"]["education"],
                "degree": item["Titel"],
                "last_name": item["Name"],
                "party": item["Wahlkreis_ParteiKurzBez"],
                "pre_last_name" : item['Namenszusatz']

               }

        temp["first_name"] =  item["Vorname"].split(' ', 1)[0]
        try:
            temp['middle_name'] = item['Vorname'].split(' ',1)[1]
        except:
            temp['middle_name'] = None

        if temp['party'] is None:
            temp['party'] = item['Liste_ParteiKurzBez']



        temp["uuid"] =  item['Vorname'] + item['Name'] + temp['party']+ 'cand17'


        if item['Geschlecht'] == 'm':
            temp["gender"] =  'male'
        else:
            temp['gender'] = 'female'

        try:
            
            temp["age"] = int(item["Geburtsjahr"])  # derzeit nur der Jahrgang
        except:
            temp["age"] = None

        state_map = {'NW': 'Nordrhein-Westfalen',
                    'BW': 'Baden-Württemberg',
                    'NI': 'Niedersachsen',
                    'SH': 'Schleswig-Holstein',
                    'BY': 'Bayern',
                    'RP': 'Rheinlandpfalz',
                    'MV': 'Mecklenburg-Vorpommern',
                    'SN': 'Sachsen',
                    'HE': 'Hessen',
                    'BE': 'Berlin',
                    'SL': 'Saarland',
                    'ST': 'Sachsen-Anhalt',
                    'HH': 'Hamburg',
                    'BB': 'Brandenburg',
                    'HB': 'Bremen',
                    'TH': 'Thüringen'
                }


        try:
            temp["list_name"] = "Landesliste " + state_map[item['Liste_Land']]
        except:
            temp["list_name"] = None

        try:
            temp["list_nr"] = int(item["Liste_Platz"])
        except:
            temp['list_nr'] = None
        try:
            temp["city"] = item['Wohnort']
            temp['city_birth'] = item['Geburtsort']
        except:
            temp['city_birth'] = None
            temp['city'] = None


        #NRW Data
        for item3 in data_abewatch['profiles']:

            if (item3['personal']['first_name'] == temp['first_name'] or
                        item3['personal']['first_name'] == item['Vorname']
                ) and item3['personal']['last_name'] == temp['last_name']:

                # foto nur dann, wenn es kein dummy foto ist
                if item3["personal"]["picture"][
                    "url"] != "https://www.abgeordnetenwatch.de/sites/abgeordnetenwatch.de/files/default_images/profil_dummy_0.jpg":
                    temp["img"] = item3["personal"]["picture"]["url"]
                break
                # nicht jeder hat einen Listenplatz
            else:
                temp["img"] = None

        if item["Wahlkreis_Nr"] is not None:
            for item2 in district['districts']:
                if int(item2['district_id']) == item["Wahlkreis_Nr"]:
                    temp['district_uuid'] = item2['uuid']
                    break

                temp['district_uuid'] = None

        else:
            temp['district_uuid'] = None


        # nrw info
        for row in nrw["k"]:
            if fuzz.partial_ratio(row["nn"] , temp["last_name"])>90:
                if party_map[row["p"][0]] == temp["party"] or party_map[row['p'][0]] == 'Parteilos':
                    if fuzz.partial_ratio(row['vn'], item['Vorname']) > 85:
                        temp["nrw"] = give_nrw_info(row["nn"], row["vn"], row)
                        if temp['nrw']['img'] is not None:
                            temp['img'] = temp['nrw']['img']
                        temp['count']  = row['id']

                        break
                #else:
                #    print(row['vn'], temp['first_name'], item['Vorname'], row['nn'], item['Name'], temp['party'])

            else:
                temp["nrw"] = None


        # check if kand is in parliament

        for kand in ywinner.find_all('Personendaten'):
            if kand['Vorname']== item['Vorname'] and kand['Geburtsdatum'] == str(temp['age']) and kand['Name'] == temp['last_name']:
                temp['member'] = 1
                countwin +=1
                print(countwin)
                break
            else:
                temp['member'] = 0

        data_list.append(temp)

        if temp['party'] not in all_party_control:
            all_party.append({"value": temp["party"] , "synonyms": [temp["party"]]})
            all_party_control.append(temp['party'])

        vornamen.append({"value": temp["first_name"] , "synonyms": [temp["first_name"], item['Vorname']]})
        nachnamen.append({"value": temp["last_name"], "synonyms": [temp["last_name"]]})


    # go through kandidatencheck_liste and check if there are candidates in nrw which are not in agbewatch
    counter = 0
    for otherrow in data_list:
        if otherrow['nrw'] is not None:
            exist = False
            for row in nrw["k"]:
                if otherrow['count'] == row['id']:
                    exist = True
                    break
            if exist == False:
                print(otherrow['first_name'], ortherrow['last_name'], otherrow['party'])





    final = {"list": data_list}

    # write transformed short json in output file
    with open(output_file, "w", encoding="utf8") as output_file:
        json.dump(final,output_file,  ensure_ascii=False)

    with open("apiai_entities_vorname.json" ,  "w", encoding="utf8") as output_fileai:
        json.dump(vornamen,output_fileai,  ensure_ascii=False)
    with open("apiai_entities_nachname.json", "w", encoding="utf8") as output_fileai2:
        json.dump(nachnamen, output_fileai2, ensure_ascii=False)
    with open("apiai_entities_all_party.json" ,  "w", encoding="utf8") as output_fileai3:
        json.dump(all_party,output_fileai3,  ensure_ascii=False)

    return




def wknr_to_uuid(wknr):
    with open('wahlkreis_info.json') as f:
        districts = json.load(f)

    for item in districts['districts']:
        if item['id'] == wknr:
            uuid = item['uuid']
            break
    return uuid



def wahl2013(wk_nummer):
    """
    Args: wk_nummer (str):   wahlkreisId
                            999 steht für Bundesgebiet

    Yields: wahlergebnisse_2013 im wahlkreis wk_nummer (dict)
    """

    wk_nummer_int = int(wk_nummer)


    # Take data from the election 2013
    wahl = pd.read_csv("wahlergebnisse_2013.csv", delimiter = ";")

    # Parteien, die 2013 angetreten sind
    parteien = ["CDU", "SPD", "FDP", "DIE LINKE", "GRÜNE", "CSU", "PIRATEN",
           "NPD", "Tierschutzpartei", "REP", "ÖDP", "FAMILIE", "Bündnis 21/RRP",
           "RENTNER", "BP", "PBC", "BüSo", "DIE VIOLETTEN", "MLPD",
           "Volksabstimmung", "PSG", "AfD", "BIG", "pro Deutschland", "DIE RECHTE",
           "DIE FRAUEN", "FREIE WÄHLER", "Nichtwähler", "PARTEI DER VERNUNFT",
           "Die PARTEI", "B", "BGD", "DKP", "NEIN!", "Übrige"]


    # wahl 2013 Bundesgebiet komplett
    temp_wahl_2013 = {}
    # set the index to the Nr Column in wahl (wahlergebnisse 2013) in order to query wahlkreis
    #  nr corresponds to wk_nummer
    wahl.set_index = ["Nr"]
    # Nr 999 ist der Index Bundesgebiet
    wk_wahl_2013 = wahl.loc[wahl.Nr ==wk_nummer_int]

    for partei in parteien:
        res = (wk_wahl_2013[partei]/wk_wahl_2013["Gültige"])[wk_wahl_2013.index[0]]

        if np.isnan(res) == True:
            res = float(0)
        temp_wahl_2013[partei] = res

    temp_wahl_2013["wahlbeteiligung"]  = (wk_wahl_2013["Wähler"]/wk_wahl_2013["Wahlberechtigte"])[wk_wahl_2013.index[0]]
    bundesgebiet_wahl_2013 = temp_wahl_2013

    return temp_wahl_2013






def plz_ort_finder(item, ort_plz_wk, take_city = False):
    """
    Args:
        item (dict): element item of wk["constituencies"]
    Yields:
        a list of plz and a list of orte
    """
    # plz
    plz = []
    ort = []
    for area in item["areacodes"]:


        # add leading 0 to 4 digit plz
        if len((area["code"])) == 4:
            code_plz = "0"+area["code"]
        else:
            code_plz = area["code"]
        # cityname api from PLZ
        if take_city == True:
            city_name = ort_finder(code_plz,ort_plz_wk)
        else:
            city_name = None
        ort.append(city_name)
        plz.append(code_plz)
    orte = list(set(ort))
    return [plz,orte]






def ort_finder(plz, ort_plz_wk,api = 0):
    """
    ARGS:
        plz (str):  5 digit number
        api (int):  if api == 1, it uses the plz api to get town
    Yields:
        the towns name, given by plz api, here already stored in plz_ort_wk.json
    """

    if api == 1:
        try:
            the_ort = json.loads(requests.get("http://api.zippopotam.us/de/"+code_plz).text)["places"][0]["place name"]
        except:
            the_ort = None
    else:
        for key, ort in ort_plz_wk.items():
            if plz in ort["plz"]:
                the_ort = key



    return  the_ort


def bundesland_finder(wahlkreisId_str, wk_bundesland):
    """
    Args:
        wahlkreisId_str (str) : "1"-- "299" Wahlkreis ID

    Yields:
        land (str):  corresponding Bundesland
    """
    wahlkreisId = int(wahlkreisId_str)

    for bundesland, wkID in wk_bundesland.items():
        if wahlkreisId in wkID["wahlkreisId"]:
            land = bundesland

    return land


def kandidaten_und_meta(wahlkreis_uuid,alle):
    """
    Args:
        wahlkreisId (str):

    yields:
        kandidaten_liste (dict):   "uuid":
                                   "vorname":
                                   "nachname":
                                   "parteien":
                                   "listenplatz":
                                   "jahrgang":

        meta (dict):   avg_alter
                        anzahl_kandidaten

    """
    kand_liste = []
    counter = 0
    alter = []
    sex = []
    for kandidat in alle["list"]:
        try:
            if kandidat["district_uuid"] == wahlkreis_uuid:
                # liste uuid
                kand_liste.append( kandidat["uuid"]
                                   #"vorname": kandidat["vorname"],
                                   #"nachname": kandidat["nachname"],
                                   #"parteien": kandidat["parteien"],
                                   #"listenplatz":kandidat["listenplatz"],
                                   #"jahrgang": kandidat["alter"]
                                  )
                # Anzahl der Kandidaten in WK + 1
                counter += 1
                alter.append(kandidat["age"])
                sex.append(kandidat["gender"])
        except:
            free = 0

    alter = [x for x in alter if x is not None]
    #alter = [int(x) for x in alter]
    quote = sex.count("female") / len(sex)
    females_total = sex.count("female")
    meta = {"avg_age": np.mean(alter), "total_candidates": counter, "quota_female": quote, "females_total" : females_total}

    return [kand_liste, meta]





