import json
import requests
from shutil import copyfile
from datetime import datetime
import numpy as np
import pandas as pd
import re



def update():

    # download data from abgeordnetenwatch

    # option =  (1 == 'deputies', 2 == 'candidates', 3 = 'constituencies

    parliament = 'Bundestag'
    kind_of_people  = 'candidates'
    output_file_abgeordnetenwatch = 'abgeordnetenwatch.json'
    abgewatch_data_file = output_file_abgeordnetenwatch

    # make backup json
    date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    copyfile(output_file_abgeordnetenwatch, 'abgeordnetenwatch_backup_'+date+'.json')
    
    
    #abgeordnetenapi(parliament, kind_of_people , output_file_abgeordnetenwatch )
    
    
    
    # create nrw_kandidaten  from Kandidatencheck-files

    check_short = 'kandidatencheck_2108.json'
    check_long = 'kandidatencheck_erweitert_2108.json'
    nrw_kandidaten_json = 'nrw_kandidaten.json'
    pic_size = 'm'   # 'xs', 's', 'm', 'l'
    
    trafo_kandidatencheck(check_short, check_long, nrw_kandidaten_json , pic_size)
    print('update ' + nrw_kandidaten_json)
    
    
    # create all_kandidaten
    
    alle_kandidaten_json = 'alle_kandidaten.json'
    
    abgewatch_to_alle(abgewatch_data_file, nrw_kandidaten_json, alle_kandidaten_json)
    print('update ' + alle_kandidaten_json)

    
    
    # create wahlkreis_info
    wahlkreis_info_json = 'wahlkreis_info.json'
    
    # make backup 
    date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    #copyfile(wahlkreis_info_json , 'wahlkreis_info_backup_'+date+'.json')
    
    # make wahlkreis_info_json
    wahlkreis_info(alle_kandidaten_json, wahlkreis_info_json)
    print('update ' + wahlkreis_info_json)

    
    
    # create api.ai entities





    return print('Done')
    


def wahlkreis_info(alle_kandidaten_json, wahlkreis_info_json):
    '''
    ARGS:
        alle_kandidaten_json (str):  
        wahlkreis_info_json (str):   file name of the creation of wahlkreis_info

    '''  
    
    # set take_city to be true
    take_city = True
    api = 0   #  0: use file ort_plz_wk, 1 use api
    
     
    with open(alle_kandidaten_json) as file:
        alle = json.load(file)
    
    wahlkreis_plz_json = 'wahlkreis_plz.json'
    bundesland_wahlkreisId = 'bundesland_wahlkreisId.json'
    ort_plz_wk = 'ort_plz_wk.json'
    

    

    with open(wahlkreis_plz_json) as file2:
        wk = json.load(file2)

    with open(bundesland_wahlkreisId) as f:
        wk_bundesland = json.load(f)

    with open(ort_plz_wk) as f:
        ort_plz_wk = json.load(f)






    wkinfo = []
    for item in wk['constituencies']:

        wahlkreisId = item['number']
        wahlkreis_uuid = item['uuid']
        # plz, orte
        plz_ort = plz_ort_finder(item,  ort_plz_wk, take_city),
        kandmeta = kandidaten_und_meta(wahlkreis_uuid,alle)

        wkinfo.append({ 'district_id': item['number'],
                                'district':  item['name'],
                                'election_13': wahl2013(wahlkreisId),
                                'uuid': item['uuid'],
                                'state': bundesland_finder(wahlkreisId,wk_bundesland),
                                'plz': plz_ort[0][0],
                                'cities': plz_ort[0][1],
                                'candidates':kandmeta[0],
                                'meta': kandmeta[1]
                                 })
    wkinfo2 = {}
    wkinfo2['districts'] = wkinfo
    
    with open(wahlkreis_info_json, 'w', encoding='utf8') as outfile:  
        json.dump(wkinfo2, outfile, ensure_ascii=False)
    
    return




def trafo_kandidatencheck(short_json, long_json, output_json, pic_size = 'm'):
    """ Adds the picture URL from the long Kandidatencheck_json to the short_candidatencheckjson
        

    Args:
        short_json (str): the file of the short and nice json
        long_json (str): the file of the long, ugly json
        output_json (str): the name of the new created output file
        pic_size (str):  pic size \in ['l','m','s','xs'] 
        
    Yields:
        creates a file with the new picture
        if there is no picture for the candidate, it writes an empty string '' instead.
        
        Further, we take away the list from the parteien key, resulting in a single string

    """
    with open(short_json) as input_file:
        short = json.load(input_file)

    with open(long_json) as input_file:
        long = json.load(input_file)
    
    for index,item in enumerate(short['list']):
        # take away the list from parteien
        short['list'][index]['parteien'] = short['list'][index]['parteien'][0]

    # get picture from erweiterte version
        for look in long['k']:
            if look['id'] == item['id']:
                try:
                    short['list'][index]['img'] = look['img'][pic_size]
                except:
                    short['list'][index]['img'] = None


    # get videolink


    #


    # write extended short json in output file
    with open(output_json, 'w', encoding='utf8') as output_file:
        json.dump(short,output_file,  ensure_ascii=False)
    
    return 



    
    
    
def abgeordnetenapi(parliament, option, file_name):

    # option = value 1-3 or one of the strings
    if option == 1:
        list_kind = 'deputies'
    elif option ==2:
        list_kind = 'candidates'
    elif option == 3:
        list_kind = 'constituencies'
    else:
        list_kind = option

    # get ID for the parliaments of interest
    r = requests.get('https://www.abgeordnetenwatch.de/api/parliaments.json')
    parliaments = r.json()

    for parli in parliaments['parliaments']:
        if parli['name'] == parliament:
            id_parliament= parli['uuid']
      
    print('request adress ist\n https://www.abgeordnetenwatch.de/api/parliament/'+id_parliament+'/'+list_kind+'.json')

    # get data from current Bundestag
    r = requests.get('https://www.abgeordnetenwatch.de/api/parliament/'+id_parliament+'/'+list_kind+'.json').json()
    with open(file_name, 'w') as output_file:
        json.dump(r, output_file)
    output_file.close()

    print('Daten wurden erfolgreich von der abgeordnetenwatch API geladen und in den entsprechenden Dateien gespeichert.')

    return


def find_id(last_name,first_name,nrw):
    '''
    Args 
        last_name (str): last_name from abgeordnetenwatch
        first_name (str): first_name from abgeordnetenwatch
        wk_id (str): wahlkreis ID from agbeordnetenwatch
    Yields
        corresponding Id (str) from nrw kandidaten_check
    '''

    for row in nrw['list']: 
        if row['nachname'] == last_name:
            if row['vorname'] == first_name:
                nrw_info = {}
                #nrw_info['id'] = row['id']
                try:
                    nrw_info['pledges'] = row['wahlversprechen']
                except:
                    nrw_info['pledges']  = None
                try:
                    nrw_info['profession'] = row['beruf']
                except:
                    nrw_info['profession'] = None

                try:
                    nrw_info['img'] = 'http:'+ row['img']
                except:
                    nrw_info['img'] = None

                try:
                    string = requests.get(row['videoJsonp']).text
                    m = re.search('143/(.+?),(.+?).mp4', string)
                    split = m.group(0).split(',')
                    file_id = split[0] + split[4]
                    nrw_info['video'] = 'http://ondemand-ww.wdr.de/medp/fsk0/' + file_id + '.mp4'
                except:
                    nrw_info['video'] = None

                try:
                    nrw_info['interests'] = row['interessen']
                except:
                    nrw_info['interests'] = None

                break
        else:
            nrw_info = None

    return nrw_info




def abgewatch_to_alle(kandidaten_alle, nrw_kandidaten, output_file):
    '''
    Args:
        kandidaten_alle (str): 
        nrw_kandidaten (str):
        output_file (str)
        
    Yields
        stores a json in output_file with the same keys as nrw_kandidaten. 
        E.g.:   {'alter': '1997',
                 'beruf': 'Angestellte',
                 'degree': None,
                 'education': None,
                 'id': '',
                 'listenplatz': '13',
                 'nachname': 'Hügelschäfer',
                 'parteien': 'DIE LINKE',
                 'uuid': '1c2427a9-7561-45a1-8d9a-0f147429849c',
                 'vorname': 'Kristin',
                 'wahkreis_uuid': '57ca45cc-2b61-4010-a8aa-4a87e83119dc',
                 'wahlkreis': 'Odenwald',
                 'wahlkreisId': '187'}

    Note. No PLZ, since this can be related by wahlkreisId
    '''

    # laden des abgeordnetenwatch kandidaten files
    with open(kandidaten_alle) as data_file:    
        data = json.load(data_file)  
    with open(nrw_kandidaten) as file:
        nrw = json.load(file)
    # erstelle liste
    data_list = []
    vornamen = []
    nachnamen = []
    # how to erstelle kandidaten_file
    for item in data['profiles']:
        if item['personal']['last_name'] != 'Testuser': # there is one test_user in the data




            temp = {'uuid': item['meta']['uuid'],
                    #personal
                    'profession':  item['personal']['profession'],
                    'education': item['personal']['education'],
                    'degree': item['personal']['degree'],
                    'last_name': item['personal']['last_name'],
                    'party': item['party'],
                    'first_name': item['personal']['first_name'],
                    'gender': item['personal']['gender']
                   }
            try:
                if (item['meta']['uuid'] == '3f466bf5-aae1-4f1e-8f6e-6679b310f2e0') and (item['personal']['birthyear'] == '2017'):
                    temp['age'] = 1989
                else:
                    temp['age'] = int(item['personal']['birthyear'])  # derzeit nur der Jahrgang

            except:
                temp['age'] = None
            # foto nur dann, wenn es kein dummy foto ist
            if item['personal']['picture']['url'] != 'https://www.abgeordnetenwatch.de/sites/abgeordnetenwatch.de/files/default_images/profil_dummy_0.jpg':
                temp['img'] =  item['personal']['picture']['url']
            # nicht jeder hat einen Listenplatz
            else:
                item['img'] = None

            try:
                temp['list_name'] = item['list']['name']
                temp['list_nr'] = int(item['list']['position'])
            except:
                temp['list_name'] = None
                temp['list_nr'] = None

            if item['constituency'] != []:
                #temp['district']  = item['constituency']['name']
                #temp['district_id'] = item['constituency']['number']
                temp['district_uuid'] =  item['constituency']['uuid']
            else:
                #temp['disctrict']  = None
                #temp['district_id'] = None
                temp['district_uuid'] = None
            #NRW Data


            temp['nrw'] =  find_id(item['personal']['last_name'],item['personal']['first_name'],nrw)

            # male candidates
            male_candidates = ['618c50ab-4eba-48bb-b85d-3f6bfcfc9cae',
                                '1016482c-da2b-46dc-9835-0cdd5e1b54ed',
                                '644bc016-9652-4b32-bd2b-fba4f5c05b8a',
                                 'da6e09e2-af3f-43c8-8a64-2fba978d63e3',
                                 'c29a6e79-3e46-400d-9cb8-117a831a5ca7',
                                 '1eacca1e-cb17-4b83-a3e1-013a1493e718',
                                 'a797e17d-52e5-445c-9f10-a124cda7320a',
                                 '36d0c560-0582-4a3f-8ff5-c71ef9d1373a',
                                 'e7326871-6fdc-485c-a7b9-e6ad18d84944',
                                 'fe71f013-e6fa-469e-b8f9-1a08cacac071',
                                 'a4c94792-122a-4bfd-8712-bcddef8ff5e2',''
                                 '57e06956-8616-4d85-ac4a-0eca8b8c2ee5',
                                 'c9a683bb-24de-437a-91d4-465dbc28d09d']
            if temp['uuid'] in male_candidates:
                temp['gender'] = 'male'

            vornamen.append({'value': temp['first_name'] , 'synonyms': [temp['first_name']]})
            nachnamen.append({'value': temp['last_name'], 'synonyms': [temp['last_name']]})
            data_list.append(temp)

    # go through kandidatencheck_liste
    '''
    for row in nrw['list']:
        exists = False
        for testing in data_list:
            if row['nachname'] == testing['last_name']:
                if row['vorname'] == testing['first_name']:
                    # check if name already exists
                    exists = True
        if exists == False:
            temp = {}
            temp['first_name'] = row['vorname']
            temp['last_name']  = row['nachname']
            temp['uuid'] = row['id']



            nrw_info = {}
            # nrw_info['id'] = row['id']
            try:
                nrw_info['pledges'] = row['wahlversprechen']
            except:
                nrw_info['pledges'] = None
            try:
                nrw_info['profession'] = row['beruf']
            except:
                nrw_info['profession'] = None

            try:
                nrw_info['img'] = row['img']
            except:
                nrw_info['img'] = None

            try:
                string = requests.get(row['videoJsonp']).text
                m = re.search('143/(.+?),(.+?).mp4', string)
                split = m.group(0).split(',')
                file_id = str(split[0] + split[4])
                nrw_info['video'] = 'http://ondemand-ww.wdr.de/medp/fsk0/' + file_id + '.mp4'
            except:
                nrw_info['video'] = None

            try:
                nrw_info['interests'] = row['interessen']
            except:
                nrw_info['interests'] = None


            temp['nrw'] = nrw_info
            vornamen.append({'value': temp['first_name'], 'synonyms': [temp['first_name']]})
            nachnamen.append({'value': temp['last_name'], 'synonyms': [temp['last_name']]})
            data_list.append(temp)
    '''



    final = {'list': data_list}

    # write transformed short json in output file
    with open(output_file, 'w', encoding='utf8') as output_file:
        json.dump(final,output_file,  ensure_ascii=False)

    with open('apiai_entities_vorname.json' ,  'w', encoding='utf8') as output_file:
        json.dump(vornamen,output_file,  ensure_ascii=False)
    with open('apiai_entities_nachname.json', 'w', encoding='utf8') as output_file:
        json.dump(nachnamen, output_file, ensure_ascii=False)

    return
    





def wahl2013(wk_nummer):
    '''
    Args: wk_nummer (str):   wahlkreisId
                            999 steht für Bundesgebiet
                            
    Yields: wahlergebnisse_2013 im wahlkreis wk_nummer (dict)
    '''
    
    wk_nummer_int = int(wk_nummer)
    
    
    # Take data from the election 2013
    wahl = pd.read_csv('wahlergebnisse_2013.csv', delimiter = ';')
    
    # Parteien, die 2013 angetreten sind
    parteien = ['CDU', 'SPD', 'FDP', 'DIE LINKE', 'GRÜNE', 'CSU', 'PIRATEN',
           'NPD', 'Tierschutzpartei', 'REP', 'ÖDP', 'FAMILIE', 'Bündnis 21/RRP',
           'RENTNER', 'BP', 'PBC', 'BüSo', 'DIE VIOLETTEN', 'MLPD',
           'Volksabstimmung', 'PSG', 'AfD', 'BIG', 'pro Deutschland', 'DIE RECHTE',
           'DIE FRAUEN', 'FREIE WÄHLER', 'Nichtwähler', 'PARTEI DER VERNUNFT',
           'Die PARTEI', 'B', 'BGD', 'DKP', 'NEIN!', 'Übrige']


    # wahl 2013 Bundesgebiet komplett
    temp_wahl_2013 = {}
    # set the index to the Nr Column in wahl (wahlergebnisse 2013) in order to query wahlkreis
    #  nr corresponds to wk_nummer
    wahl.set_index = ['Nr']
    # Nr 999 ist der Index Bundesgebiet
    wk_wahl_2013 = wahl.loc[wahl.Nr ==wk_nummer_int]

    for partei in parteien:
        res = (wk_wahl_2013[partei]/wk_wahl_2013['Gültige'])[wk_wahl_2013.index[0]]

        if np.isnan(res) == True:
            res = float(0)
        temp_wahl_2013[partei] = res

    temp_wahl_2013['wahlbeteiligung']  = (wk_wahl_2013['Wähler']/wk_wahl_2013['Wahlberechtigte'])[wk_wahl_2013.index[0]]
    bundesgebiet_wahl_2013 = temp_wahl_2013
    
    return temp_wahl_2013
    
    
    
    
    

def plz_ort_finder(item, ort_plz_wk, take_city = False):
    '''
    Args:
        item (dict): element item of wk['constituencies']
    Yields:
        a list of plz and a list of orte
    '''
    # plz
    plz = []
    ort = []
    for area in item['areacodes']:
        plz.append(area['code'])

        # add leading 0 to 4 digit plz
        if len((area['code'])) == 4:
            code_plz = '0'+area['code']
        else:
            code_plz = area['code']
        # cityname api from PLZ
        if take_city == True:
            city_name = ort_finder(code_plz,ort_plz_wk)
        else:
            city_name = None
        ort.append(city_name)  
    orte = list(set(ort))
    return [plz,orte] 






def ort_finder(plz, ort_plz_wk,api = 0):
    '''
    ARGS:
        plz (str):  5 digit number
        api (int):  if api == 1, it uses the plz api to get town
    Yields:
        the towns name, given by plz api, here already stored in plz_ort_wk.json
    '''
    
    if api == 1:
        try:
            the_ort = json.loads(requests.get('http://api.zippopotam.us/de/'+code_plz).text)['places'][0]['place name']
        except:
            the_ort = None
    else:
        for key, ort in ort_plz_wk.items():
            if plz in ort['plz']:
                the_ort = key
        
            
            
    return  the_ort


def bundesland_finder(wahlkreisId_str, wk_bundesland):
    '''
    Args:
        wahlkreisId_str (str) : '1'-- '299' Wahlkreis ID

    Yields:
        land (str):  corresponding Bundesland
    '''
    wahlkreisId = int(wahlkreisId_str)

    for bundesland, wkID in wk_bundesland.items():
        if wahlkreisId in wkID['wahlkreisId']:
            land = bundesland
    
    return land


def kandidaten_und_meta(wahlkreis_uuid,alle):
    '''
    Args:
        wahlkreisId (str): 
        
    yields: 
        kandidaten_liste (dict):   'uuid':
                                   'vorname': 
                                   'nachname':
                                   'parteien':
                                   'listenplatz':
                                   'jahrgang':
        
        meta (dict):   avg_alter
                        anzahl_kandidaten

    '''
    kand_liste = []
    counter = 0
    alter = []
    sex = []
    for kandidat in alle['list']:
        try:
            if kandidat['district_uuid'] == wahlkreis_uuid:
                # liste uuid
                kand_liste.append( kandidat['uuid']
                                   #'vorname': kandidat['vorname'],
                                   #'nachname': kandidat['nachname'],
                                   #'parteien': kandidat['parteien'],
                                   #'listenplatz':kandidat['listenplatz'],
                                   #'jahrgang': kandidat['alter']
                                  )
                # Anzahl der Kandidaten in WK + 1
                counter += 1
                alter.append(kandidat['age'])
                sex.append(kandidat['gender'])
        except:
            free = 0

    alter = [x for x in alter if x is not None]
    #alter = [int(x) for x in alter]
    quote = sex.count('female') / len(sex)
    females_total = sex.count('female')
    meta = {'avg_age': np.mean(alter), 'total_candidates': counter, 'quota_female': quote, 'females_total' : females_total}
    
    return [kand_liste, meta]





