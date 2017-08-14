import json
import requests
from shutil import copyfile
from datetime import datetime
import numpy as np
import pandas as pd



def update():

	# download data from abgeordnetenwatch

	Parlament = 'Bundestag'
	# option =  (1 == 'deputies', 2 == 'candidates', 3 = 'constituencies
	kind_of_people = 'candidates' 
	abgewatch_data_file =  'abgeordnetenwatch.json'
	
	# make backup json
	date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
	copyfile(abgewatch_data_file, 'abgeordnetenwatch_backup_'+date+'.json')
	
	
	#abgeordnetenapi(parliament, kind_of_people , output_file_abgeordnetenwatch )
	
	
	
	# create nrw_kandidaten  from Kandidatencheck-files

	check_short = 'kandidatencheck_0108.json'
	check_long = 'kandidatencheck_erweitert_0108.json'
	nrw_kandidaten_json = 'nrw_kandidaten.json'
	pic_size = 'm'   # 'xs', 's', 'm', 'l'
	
	trafo_kandidatencheck(check_short, check_long, nrw_kandidaten_json , pic_size)
	
	
	
	# create all_kandidaten
	
	alle_kandidaten_json = 'alle_kandidaten.json'
	
	abgewatch_to_alle(abgewatch_data_file, nrw_kandidaten_json, alle_kandidaten_json)
	
	
	
	# create wahlkreis_info
	wahlkreis_info_json = 'wahlkreis_info.json'
	
	# make backup 
	date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
	copyfile(wahlkreis_info_json , 'wahlkreis_info_backup_'+date+'.json')
	
	# make wahlkreis_info_json
	wahlkreis_info(alle_kandidaten_json, wahlkreis_info_json)
	
	
	
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
        # plz, orte
        plz_ort = plz_ort_finder(item,  ort_plz_wk, take_city),
        kandmeta = kandidaten_und_meta(wahlkreisId,alle)

        wkinfo.append({ 'wahlkreisId': item['number'],
                                'wahlkreis':  item['name'],
                                'wahl_13': wahl2013(wahlkreisId),
                                'wk_uuid': item['uuid'],
                                'bundesland': bundesland_finder(wahlkreisId,wk_bundesland),
                                'plz': plz_ort[0][0],
                                'orte': plz_ort[0][1],
                                'kandidaten':kandmeta[0],
                                'meta': kandmeta[1]
                                 })
    wkinfo2 = {}
    wkinfo2['wahlkreise'] = wkinfo
    
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
    	
    	for look in long['k']:
        	if look['id'] == item['id']:
        		try:
        			short['list'][index]['img'] = look['img'][pic_size]
        		except:
        			short['list'][index]['img'] = ''
	
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
    id_here = ''
    for row in nrw['list']: 
        if row['nachname'] == last_name:
            if row['vorname'] == first_name:
                id_here = row['id']
    
    return id_here




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
    
    # how to erstelle kandidaten_file
    for item in data['profiles']:
        if item['personal']['last_name'] != 'Testuser': # there is one test_user in the data
            temp = {'uuid': item['meta']['uuid'],
                    'id': find_id(item['personal']['last_name'],item['personal']['first_name'],nrw),
                    #personal
                    'alter': item['personal']['birthyear'],  # derzeit nur das alter
                    'beruf':  item['personal']['profession'],
                    'education': item['personal']['education'],
                    'degree': item['personal']['degree'],
                    'nachname': item['personal']['last_name'],
                    'parteien': item['party'],
                    'vorname': item['personal']['first_name'],
                    'gender': item['personal']['gender']
                   }
            # foto nur dann, wenn es kein dummy foto ist
            if item['personal']['picture']['url'] != 'https://www.abgeordnetenwatch.de/sites/abgeordnetenwatch.de/files/default_images/profil_dummy_0.jpg':
                temp['img'] =  item['personal']['picture']['url']
            # nicht jeder hat einen Listenplatz
            else:
                item['list'] = ''
            try:
                temp['listenplatz'] = item['list']['position']
            except:
                temp['listenplatz'] = ''
            if item['constituency'] != []:
                temp['wahlkreis']  = item['constituency']['name']
                temp['wahlkreisId'] = item['constituency']['number']
                temp['wahkreis_uuid'] =  item['constituency']['uuid']
            else:
                temp['wahlkreis']  = ''
                temp['wahlkreisId'] = ''
                temp['wahkreis_uuid'] = ''
            data_list.append(temp)
        
    final = {'list': data_list}

	# write transformed short json in output file
    with open(output_file, 'w', encoding='utf8') as output_file:
        json.dump(final,output_file,  ensure_ascii=False) 


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
            city_name = ''
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
    		the_ort = ''
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


def kandidaten_und_meta(wahlkreisId,alle):
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
        
        if kandidat['wahlkreisId'] == wahlkreisId:
            kand_liste.append({'uuid': kandidat['uuid'],
                               'vorname': kandidat['vorname'],
                               'nachname': kandidat['nachname'],
                               'parteien': kandidat['parteien'],
                               'listenplatz':kandidat['listenplatz'],
                               'jahrgang': kandidat['alter']
                              })
            # Anzahl der Kandidaten in WK + 1
            counter += 1 
            
            
            alter.append(kandidat['alter'])
            sex.append(kandidat['gender'])
    alter = [x for x in alter if x is not None]
    alter = [int(x) for x in alter]    
    quote = sex.count('female')/len(sex)
    meta = {'avg_alter': np.mean(alter), 'anzahl_kandidaten': counter, 'Frauenquote': quote}
    
    return [kand_liste, meta]





