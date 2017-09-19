import numpy as np
import csv
from fuzzywuzzy import fuzz
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from pathlib import Path

DATA_DIR = Path(__file__).absolute().parent










def make_kerg_to_df(kerg):

    #  parteien Kurzbezeichnung und Bezeichnung
    party_abbrv = pd.read_csv(str(DATA_DIR/'btw17_parteien.csv'), delimiter=';')
    long_names = list(party_abbrv['BEZEICHNUNG'].unique())

    with open(kerg, 'r') as inp, open(str(DATA_DIR/'kerg_edit.csv'), 'w') as out:
        writer = csv.writer(out)
        for index, row in enumerate(csv.reader(inp)):
            # take out first 2 rows
            if index == 2:
                stringA = ''
                for ele in row:
                    stringA += ele
                splitA = stringA.split(';')
            if index == 3:
                stringB = ''
                for ele in row:
                    stringB += ele
                splitB = stringB.split(';')
            if index == 4:
                stringC = ''
                for ele in row:
                    stringC += ele
                splitC = stringC.split(';')
                header = ''
                extention = []
                for nr in range(0, len(splitA)):
                    A = splitA[nr]
                    cntA = 1
                    cntB = 1
                    cntC = 1
                    while A == '' and nr > 3:
                        A = splitA[nr - cntA]
                        cntA += 1
                    for i, value in party_abbrv['BEZEICHNUNG'].iteritems():
                        if fuzz.partial_ratio(A, value) > 95:
                            A = party_abbrv.loc[party_abbrv['BEZEICHNUNG'] == value]['KURZBEZEICHNUNG'].values[0]
                            break
                    B = splitB[nr]
                    while B == '' and nr > 3:
                        B = splitB[nr - cntB]
                        cntB += 1
                    C = splitC[nr]
                    while C == '' and nr > 3:
                        C = splitC[nr - cntC]
                        cntC += 1
                    header += (A + ' ' + B + ' ' + C).rstrip()
                    if 3 <= nr <= 6:
                        extention.append((' ' + B + ' ' + C).rstrip())
                    if nr != len(splitA) - 1:
                        header += ';'
                writer.writerow([header])
            # create body
            if index >= 5:
                # print(row)
                writer.writerow(row)


    return extention


def result(wk_nummer, extention):
    """
    Args: wk_nummer (str):   wahlkreisId
                            999 steht für Bundesgebiet

    Yields: dictionary with results of keys
    """

    party_abbrv = pd.read_csv(str(DATA_DIR/'btw17_parteien.csv'), delimiter=';')



    keys = {extention[0]: 'first17',
            extention[1]: 'first13',
            extention[2]: 'second17',
            extention[3]: 'second13'}
    # Take data from the election 2013
    data = pd.read_csv(str(DATA_DIR/"kerg_edit.csv"), delimiter=";")
    data.loc[data['Gebiet'] == 'Bundesgebiet', 'Nr'] = 999

    # Parteien, die 2013 angetreten sind
    parteien = party_abbrv[party_abbrv['TYP'] == 'Partei']

    # wahl 2013 Bundesgebiet komplett
    temp = {}
    # set the index to the Nr Column in wahl (wahlergebnisse 2013) in order to query wahlkreis
    #  nr corresponds to wk_nummer
    data.set_index = ["Nr"]
    # Nr 999 ist der Index Bundesgebiet
    data1 = data.loc[data['Nr'] == wk_nummer]
    data_wk = data1.loc[data1['gehört zu'] != 99]
    for element in extention:
        temp[keys[element]] = {}
        for party in parteien['KURZBEZEICHNUNG']:
            temp[keys[element]][party] = (data_wk[party + element].iloc[0] / data_wk['Gültige' + element].iloc[0])
        temp[keys[element]]["voters"] = (
        data_wk["Wähler" + element].iloc[0] / data_wk["Wahlberechtigte" + element].iloc[0])
        temp[keys[element]]["voters_invalid"] = (
        data_wk["Ungültige" + element].iloc[0] / data_wk["Wahlberechtigte" + element].iloc[0])

    temp['name'] = data_wk['Gebiet'].iloc[0]

    # if np.isnan(res) == True:
    #    res = float(0)
    #   temp[party] = res

    # bundesgebiet_wahl_2013 = temp_wahl_2013

    return temp


def plot_vote(wk_nummer,extention):

    # run result
    data = result(wk_nummer,extention)

    # color scheme for the different parties
    color_dict = {"Sonstige": "grey",
                  "DIE LINKE": "#96276E",
                  "FDP": "#F6BB00",
                  "AfD": "#34A3D2",
                  "SPD": "#DB4240",
                  "CSU": "#373737",
                  "CDU": "#373737",
                  "CDU/CSU": '#373737',
                  "GRÜNE": "#4BA345",
                  "PIRATE": "#FF8800"
                  }



    values = []
    values13 = []
    label = []
    colors = []
    diff = []
    election17 = 'second17'
    election13 = 'second13'

    top7 = ['CDU', 'CSU', 'SPD', 'DIE LINKE', 'GRÜNE', 'FDP', 'AfD']

    # create base table
    for party in top7:
        if round(data[election17][party] * 100, 1) > 0:
            values.append(round(data[election17][party] * 100, 1))
            values13.append(round(data[election13][party] * 100, 1))
            key = party
            label.append(key)
            try:
                colors.append(color_dict[key])
            except:
                colors.append('grey')

            if label == ['CDU', 'CSU']:
                values = [sum(values)]
                values13 = [sum(values13)]
                label = ['CDU/CSU']
                colors = [color_dict[label[0]]]
    # label = ['CDU/CSU', 'SPD', 'Linke', 'Grüne', 'FDP', 'AfD', 'Sonstige']

    diff = list(np.array(values) - np.array(values13))
    colors.append(color_dict['Sonstige'])
    label.append('Sonstige')
    values.append(100 - sum(values))
    diff.append(values[-1] - (100 - sum(values13)))

    fig = plt.figure(figsize=(10, 6))
    ax = plt.gca()
    index = np.arange(len(values))
    bar_width = 0.6
    ax.set_axisbelow(True)
    backgroundcolor = 'deeppink'
    ax.yaxis.grid(color='grey', linestyle='-')
    ax.bar(index, values, bar_width,
           color=colors
           )
    ax.set_facecolor('0.95')  # 0.95

    plt.xticks(index + bar_width / 2 - 0.3, label, fontsize=14)
    ax.tick_params(axis=u'both', which=u'both', length=0)

    plt.yticks([5, 10, 20, 30, 40, 50, 60], fontsize=16)
    plt.ylabel('Stimmenanteil in %', fontsize=16)
    xy = (index[0], values[0])
    for go in index:
        text = str(values[go]) + '%'
        ax.annotate(text, xy=(index[go] - 0.25, max(values[go] + 2, 5.5)), fontsize=16)
        # for go in index:
        di = diff[go]
        text = str(diff[go]) + '%'
        if di >= 0:
            text = '+' + text
        if values[go] < 1.8:
            col = 'k'
            ylevel = 2.5
        else:
            col = 'white'
            ylevel = 1
        ax.annotate(text, xy=(index[go] - 0.27, ylevel), color=col, fontsize=13)
    ax.set_ylim(0, max(values) + 5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    # 5% line
    plt.axhline(y=5, linewidth=2, color='k')
    plt.title('Vorläufiges Ergebnis  - Zweitstimmen \n \"'
              + data['name'] +
              '\" ', fontsize=20)
    # ax.annotate('5%', xy=(-1, 5), color = 'k', fontsize=13)
    ax.annotate('Wahlbeteiligung:    ' +
                str(round(data[election17]['voters'] * 100, 1))
                + '%\ndavon ungültig:        ' + str(round(data[election17]['voters_invalid'] * 100, 1)) + '%'
                ,
                xy=(4, 33), color='k', fontsize=13)

    #### THIS PUTS IN A DATE STAMP TO GET RID OF TEST PICTURES
    now = datetime.datetime.now()
    if now < datetime.datetime(2017, 9, 25, 3, 0, 0):    # from monday morning 3:00 no test anymore
        t = plt.text(0.1, 0.50, 'TEST', transform=ax.transAxes, fontsize=180)
        t.set_bbox(dict(facecolor='red', alpha=0.5, edgecolor='red'))


    plt.savefig(str(DATA_DIR/'../../static/bot/result_grafics/second_distric'+str(wk_nummer)+'.jpg'), bbox_inches='tight')
    plt.clf()
    plt.close(fig)

    return



###  start function


#bundeswahlleiter data
kerg = 'kerg.csv'

# make nice function from kerg  : extention is for the given header names
extention = make_kerg_to_df(kerg)

# create plot for all 999 votes
for district in range(1,300):
    plot_vote(district,extention)

# create plot for Bundesgebiet
plot_vote(999,extention)
